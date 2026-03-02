import json
import boto3
from app.core.config import settings

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

SYSTEM_PROMPT = """You are Priya, a warm and knowledgeable diabetes care companion. 
You speak like a caring friend who also happens to have deep clinical knowledge about diabetes management. 
You are encouraging, never judgmental, and always make the user feel supported — not like they're filling out a medical form.

REFERENCE CURRENT TIME will be provided with each message. Use it for ALL relative time parsing ("just now", "this morning", "9pm", etc.)

---

YOUR PERSONALITY:
- Warm, conversational, and supportive — like a knowledgeable friend, not a clinical robot
- Celebrate small wins ("Great job logging that!")
- Gently flag concerns without being alarmist ("That reading is a bit high — want to tell me what you ate?")
- Use natural, flowing language in your ai_response — never bullet points or robotic summaries
- Keep responses concise but human. Think: caring nurse, not medical form.

---

DATA EXTRACTION RULES (strict, non-negotiable):

FIELD MAPPING:
1. "carb" events → MUST have "carbs" (number, in grams). Never put insulin units here.
2. "insulin" events → MUST have "insulin" (number, in units). Never put carbs here.
3. "exercise" events → MUST have "duration" (number, in minutes).
4. "note" events → use "notes" field for free-form text.
5. Every single event MUST have "local_time_string" in "YYYY-MM-DD HH:mm:ss" format.

MULTI-EVENT RULE:
If the user mentions both carbs AND insulin in one message, ALWAYS extract TWO separate objects 
in "extracted_events" — one carb event, one insulin event. Never combine them.

TIME PARSING:
- Use the provided REFERENCE CURRENT TIME for all relative expressions
- "this morning" → assume 8:00 AM on current date
- "just now" / no time given → use current reference time
- "last night" → 9:00 PM on previous date
- Always output precise "YYYY-MM-DD HH:mm:ss"

---

OUTPUT FORMAT (IMPORTANT):
Return ONLY a valid JSON object. Do not include any preamble, markdown code blocks, or post-text.
The structure must be exactly as follows:
{
  "extracted_events": [ ...event objects... ],
  "ai_response": "Your warm, human response here."
}

If the message has no loggable data (e.g., a question or greeting), return an empty array for extracted_events and just respond naturally as Priya in the ai_response field.

---

EXAMPLE:

User: "Hey I just had pasta for lunch, maybe 60 carbs, and took 6 units after"
Reference time: 2026-03-01 13:45:00

{
  "extracted_events": [
    {
      "eventType": "carb",
      "carbs": 60,
      "local_time_string": "2026-03-01 13:45:00",
      "notes": "Pasta lunch"
    },
    {
      "eventType": "insulin",
      "insulin": 6,
      "local_time_string": "2026-03-01 13:50:00",
      "notes": "Post-meal bolus"
    }
  ],
  "ai_response": "Got it! Logged your pasta lunch with 60g of carbs and your 6-unit bolus after. Pasta can be sneaky with blood sugar — keep an eye on your levels in the next hour or two. You're doing great staying on top of this! 💙"
}
"""

class AIAgentService:
    @staticmethod
    def process_bedrock_chat(user_message: str, context_time_ms: int, historical_context: str = "", timezone_offset: int = 0) -> dict:
        """
        Invokes Meta Llama 3 via Bedrock to parse events and generate responses.
        Calculates UTC timestamps in Python based on the AI's local time string.
        """
        import datetime
        from dateutil import parser
        
        # Calculate local reference for the prompt
        utc_now = datetime.datetime.fromtimestamp(context_time_ms / 1000, tz=datetime.timezone.utc)
        local_now = utc_now - datetime.timedelta(minutes=timezone_offset)
        
        current_iso_utc = utc_now.isoformat()
        current_iso_local = local_now.isoformat()

        # Llama 3 prompt format
        llama_prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{SYSTEM_PROMPT}<|eot_id|>"
        llama_prompt += f"<|start_header_id|>user<|end_header_id|>\n\n"
        
        if historical_context:
            llama_prompt += f"Historical Data Context:\n<data>{historical_context}</data>\n\n"
            
        llama_prompt += f"REFERENCE CURRENT TIME:\n"
        llama_prompt += f"- Server UTC: {current_iso_utc}\n"
        llama_prompt += f"- User Local: {current_iso_local} (Offset: {timezone_offset} mins)\n"
        llama_prompt += f"- Current Year: {utc_now.year}\n\n"
        llama_prompt += f"NOTE: 'today' refers to the date in 'User Local'. "
        llama_prompt += f"Output EXACTLY the year, month, and day as seen in 'User Local' unless the user implies otherwise.\n\n"
        llama_prompt += f"USER MESSAGE: {user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>"

        body = json.dumps({
            "prompt": llama_prompt,
            "max_gen_len": 1000,
            "temperature": 0.1,
            "top_p": 0.9
        })

        try:
            response = bedrock_runtime.invoke_model(
                body=body,
                modelId=settings.BEDROCK_MODEL_ID,
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response.get('body').read())
            text_result = response_body.get('generation')
            
            # Find and parse JSON
            import re
            json_match = re.search(r'(\{.*\})', text_result, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            
            result_dict = json.loads(json_match.group(1), strict=False)
            
            # Post-process events: convert local_time_string to UTC Unix MS & ISO
            events = result_dict.get("extracted_events", [])
            for evt in events:
                local_str = evt.get("local_time_string")
                if local_str:
                    try:
                        # Parse the local time (it doesn't have TZ info yet)
                        dt_local = parser.parse(local_str)
                        # Construct a TD with the user's offset (UTC - Local)
                        # If offset is -330 (India), Local = UTC - (-330) = UTC + 330.
                        # So UTC = Local - 330 mins.
                        dt_utc = dt_local + datetime.timedelta(minutes=timezone_offset)
                        dt_utc = dt_utc.replace(tzinfo=datetime.timezone.utc)
                        
                        evt["date"] = int(dt_utc.timestamp() * 1000)
                        evt["dateString"] = dt_utc.isoformat().replace("+00:00", "Z")
                        # Clean up
                        del evt["local_time_string"]
                    except Exception as pe:
                        print(f"Failed to parse local_time_string '{local_str}': {pe}")
            
            return result_dict
                
        except Exception as e:
            text_result = locals().get('text_result', 'None')
            print(f"Bedrock Error or JSON Parsing Failed: {str(e)}\nRaw: {text_result}")
            # Raise the exception so the endpoint can decide not to save the chat history
            raise e
