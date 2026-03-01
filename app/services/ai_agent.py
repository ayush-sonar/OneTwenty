import json
import boto3
from app.core.config import settings

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

SYSTEM_PROMPT = """You are an intelligent clinical diabetes assistant and data extraction engine. 
Your goal is to parse natural language logging entries into strict JSON structure for MongoDB ingestion, AND provide helpful conversational insights when requested.

CRITICAL: Use the provided "REFERENCE CURRENT TIME" for ALL relative time parsing (like "9pm").

FIELD MAPPING RULES:
1. "carb" events MUST have a "carbs" (number, grams) field. Do NOT put insulin units here.
2. "insulin" events MUST have an "insulin" (number, units) field. Do NOT put carbs here.
3. "exercise" events MUST have a "duration" (number, minutes) field.
4. "note" events use the "notes" field for general text.
5. "local_time_string": ALL events MUST have this in "YYYY-MM-DD HH:mm:ss" format.

MULTI-EVENT LOGGING:
If the user mentions both carbs and insulin (e.g., "I ate 50g and took 5 units"), you MUST extract TWO separate objects in the "extracted_events" array: one for the carb and one for the insulin.

REQUIREMENTS:
1. You MUST ALWAYS output a single JSON object with "extracted_events" (array) and "ai_response" (string).
2. For relative times like "today", use the User Local reference.
3. PRECISELY calculate the "local_time_string".

Example Output for "I ate 40g and took 4 units":
{
  "extracted_events": [
    { "eventType": "carb", "carbs": 40, "local_time_string": "2026-03-01 14:00:00", "notes": "Lunch" },
    { "eventType": "insulin", "insulin": 4, "local_time_string": "2026-03-01 14:05:00", "notes": "Bolus" }
  ],
  "ai_response": "I have logged your 40g lunch and 4 units of insulin."
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
            msg = text_result if 'text_result' in locals() else 'None'
            print(f"Bedrock Error or JSON Parsing Failed: {str(e)}\nRaw: {msg}")
            return {
                "extracted_events": [],
                "ai_response": f"I couldn't process that properly due to an error: {str(e)}"
            }
