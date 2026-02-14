import * as d3 from 'd3';

/**
 * Nightscout-style Enhanced Glucose Chart
 * Matches original Nightscout UI with:
 * - Nightscout color scheme
 * - "Now" line with current reading
 * - Gray out old data
 * - Dual-axis (focus + context with brush)
 */
export class EnhancedGlucoseChart {
    constructor(containerId, settings) {
        this.container = d3.select(`#${containerId}`);

        // Handle both backend format (bg_high, bg_target_top) and ensure defaults
        const defaults = {
            units: 'mg/dl',
            bg_target_top: 180,
            bg_target_bottom: 80,
            alarm_high: 260,
            alarm_low: 70
        };

        if (settings) {
            this.settings = {
                units: settings.units || defaults.units,
                bg_target_top: settings.bg_target_top || defaults.bg_target_top,
                bg_target_bottom: settings.bg_target_bottom || defaults.bg_target_bottom,
                alarm_high: settings.bg_high || settings.alarm_high || defaults.alarm_high,
                alarm_low: settings.bg_low || settings.alarm_low || defaults.alarm_low
            };
        } else {
            this.settings = defaults;
        }

        this.margin = { top: 20, right: 80, bottom: 100, left: 60 };
        this.margin2 = { top: 430, right: 80, bottom: 30, left: 60 };
        this.data = [];
        this.treatments = [];

        // Flags to prevent infinite recursion
        this.isUpdatingFromBrush = false;
        this.isUpdatingFromZoom = false;

        // Nightscout color scheme (exact hex codes from reference)
        this.colors = {
            background: '#000000',      // Pure black background
            gridLines: '#333333',       // Subtle dark gray grid
            axisLabels: '#bdbdbd',      // Light gray for axis text
            nowLine: '#0099ff',         // Blue for "now" line
            inRange: '#00ff00',         // Green for in-range
            low: '#ff0000',             // Red for low
            high: '#ffff00',            // Yellow for high
            urgent: '#ff0000',          // Red for urgent
            targetRange: 'rgba(0, 255, 0, 0.1)', // Transparent green for target range
            old: '#808080'              // Gray for old data
        };
    }

    init() {
        // Clear any existing chart
        this.container.selectAll('*').remove();

        // Calculate dimensions - LARGER chart
        const containerRect = this.container.node().getBoundingClientRect();
        this.width = containerRect.width - this.margin.left - this.margin.right;
        this.height = 500; // Increased height

        // Create SVG
        this.svg = this.container
            .append('svg')
            .attr('width', this.width + this.margin.left + this.margin.right)
            .attr('height', this.height + this.margin.top + this.margin.bottom)
            .style('background', this.colors.background)
            .append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Create scales
        this.xScale = d3.scaleTime().range([0, this.width]);
        this.yScale = d3.scaleLinear().range([this.height, 0]);

        // Dynamic timestamp formatting (from Nightscout source)
        const formatMinute = d3.timeFormat('%H:%M');
        const formatHour = d3.timeFormat('%H:%M');
        const formatDay = d3.timeFormat('%a %d');
        const formatWeek = d3.timeFormat('%b %d');

        const tickFormat = (date) => {
            return (d3.timeMinute(date) < date ? d3.timeFormat(':%S') :
                d3.timeHour(date) < date ? formatMinute :
                    d3.timeDay(date) < date ? formatHour :
                        d3.timeMonth(date) < date ? formatDay :
                            formatWeek)(date);
        };

        // Specific BG tick values (from Nightscout source)
        const bgTickValues = [40, 55, 80, 120, 180, 260, 400];

        // Create axes with Nightscout formatting
        this.xAxis = d3.axisBottom(this.xScale)
            .tickFormat(tickFormat)
            .ticks(6);

        this.yAxis = d3.axisLeft(this.yScale)
            .tickFormat(d3.format('d'))
            .tickValues(bgTickValues);

        this.xAxis2 = d3.axisBottom(this.xScale2)
            .tickFormat(tickFormat)
            .ticks(6);

        this.yAxis2 = d3.axisRight(this.yScale2)
            .tickFormat(d3.format('d'))
            .tickValues(bgTickValues);

        // Clip path for focus area
        this.svg.append('defs').append('clipPath')
            .attr('id', 'clip')
            .append('rect')
            .attr('width', this.width)
            .attr('height', this.height);

        // Focus area (main chart)
        this.focus = this.svg.append('g')
            .attr('class', 'focus')
            .attr('clip-path', 'url(#clip)');

        // Context area (brush/overview)
        this.context = this.svg.append('g')
            .attr('class', 'context')
            .attr('transform', `translate(0,${this.margin2.top})`);

        // Add target range to focus
        this.focus.append('rect')
            .attr('class', 'target-range')
            .attr('fill', this.colors.targetRange);

        // Add threshold lines to focus
        this.addThresholdLine(this.focus, 'high-line', this.settings.alarm_high, this.colors.high);
        this.addThresholdLine(this.focus, 'target-top-line', this.settings.bg_target_top, this.colors.inRange);
        this.addThresholdLine(this.focus, 'target-bottom-line', this.settings.bg_target_bottom, this.colors.inRange);
        this.addThresholdLine(this.focus, 'low-line', this.settings.alarm_low, this.colors.low);

        // Add threshold lines to context
        this.addThresholdLine(this.context, 'context-target-top', this.settings.bg_target_top, this.colors.inRange);
        this.addThresholdLine(this.context, 'context-target-bottom', this.settings.bg_target_bottom, this.colors.inRange);

        // Create line generators
        this.line = d3.line()
            .x(d => this.xScale(new Date(d.date)))
            .y(d => this.yScale(d.sgv))
            .curve(d3.curveMonotoneX);

        this.line2 = d3.line()
            .x(d => this.xScale2(new Date(d.date)))
            .y(d => this.yScale2(d.sgv))
            .curve(d3.curveMonotoneX);

        // Add paths
        this.focus.append('path')
            .attr('class', 'glucose-line')
            .attr('fill', 'none')
            .attr('stroke', this.colors.current)
            .attr('stroke-width', 2);

        this.context.append('path')
            .attr('class', 'glucose-line-context')
            .attr('fill', 'none')
            .attr('stroke', this.colors.current)
            .attr('stroke-width', 1.5);

        // Add dots groups
        this.focus.append('g').attr('class', 'dots');
        this.context.append('g').attr('class', 'dots-context');

        // Add X-axis (time) to focus
        this.focus.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${this.height})`)
            .style('color', this.colors.axisLabels);

        // Add X-axis label
        this.focus.append('text')
            .attr('class', 'x-axis-label')
            .attr('x', this.width / 2)
            .attr('y', this.height + 40)
            .attr('text-anchor', 'middle')
            .attr('fill', this.colors.axisLabels)
            .attr('font-size', '12px')
            .text('Time');

        // Add Y-axis (glucose) to focus
        this.focus.append('g')
            .attr('class', 'y-axis')
            .style('color', this.colors.axisLabels);

        // Add Y-axis label
        this.focus.append('text')
            .attr('class', 'y-axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('x', -this.height / 2)
            .attr('y', -40)
            .attr('text-anchor', 'middle')
            .attr('fill', this.colors.axisLabels)
            .attr('font-size', '12px')
            .text(`Blood Glucose (${this.settings.units})`);

        // Add X-axis to context (brush)
        this.context.append('g')
            .attr('class', 'x-axis-context')
            .attr('transform', `translate(0,${this.height2})`)
            .style('color', this.colors.axisLabels);

        // Add X-axis label for context
        this.context.append('text')
            .attr('class', 'x-axis-context-label')
            .attr('x', this.width / 2)
            .attr('y', this.height2 + 35)
            .attr('text-anchor', 'middle')
            .attr('fill', this.colors.axisLabels)
            .attr('font-size', '11px')
            .text('Time Range');

        // Add "now" line group (will be updated with data)
        this.nowLineGroup = this.focus.append('g')
            .attr('class', 'now-line-group');

        // Create brush
        this.brush = d3.brushX()
            .extent([[0, 0], [this.width, this.height2]])
            .on('brush end', (event) => this.brushed(event));

        this.context.append('g')
            .attr('class', 'brush')
            .call(this.brush)
            .selectAll('rect')
            .attr('fill', '#0099ff')
            .attr('fill-opacity', 0.2);

        // Add zoom
        this.zoom = d3.zoom()
            .scaleExtent([1, 10])
            .translateExtent([[0, 0], [this.width, this.height]])
            .extent([[0, 0], [this.width, this.height]])
            .on('zoom', (event) => this.zoomed(event));

        this.svg.append('rect')
            .attr('class', 'zoom-rect')
            .attr('width', this.width)
            .attr('height', this.height)
            .style('fill', 'none')
            .style('pointer-events', 'all')
            .call(this.zoom);
    }

    addThresholdLine(container, className, value, color) {
        container.append('line')
            .attr('class', className)
            .attr('stroke', color)
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '5,5')
            .attr('opacity', 0.5);
    }

    updateData(entries) {
        if (!entries || entries.length === 0) return;

        this.data = entries.sort((a, b) => new Date(a.date) - new Date(b.date));

        // Update scales
        const timeExtent = d3.extent(this.data, d => new Date(d.date));
        const glucoseExtent = d3.extent(this.data, d => d.sgv);

        this.xScale.domain(timeExtent);
        this.xScale2.domain(timeExtent);

        const yDomain = [
            Math.min(this.settings.alarm_low - 20, glucoseExtent[0]),
            Math.max(this.settings.alarm_high + 20, glucoseExtent[1])
        ];

        this.yScale.domain(yDomain);
        this.yScale2.domain(yDomain);

        // Update axes
        this.focus.select('.x-axis').call(this.xAxis);
        this.focus.select('.y-axis').call(this.yAxis);
        this.context.select('.x-axis-context').call(this.xAxis2);

        // Update target range
        this.focus.select('.target-range')
            .attr('x', 0)
            .attr('y', this.yScale(this.settings.bg_target_top))
            .attr('width', this.width)
            .attr('height', this.yScale(this.settings.bg_target_bottom) - this.yScale(this.settings.bg_target_top));

        // Update threshold lines
        this.updateThresholdLine(this.focus, 'high-line', this.settings.alarm_high);
        this.updateThresholdLine(this.focus, 'target-top-line', this.settings.bg_target_top);
        this.updateThresholdLine(this.focus, 'target-bottom-line', this.settings.bg_target_bottom);
        this.updateThresholdLine(this.focus, 'low-line', this.settings.alarm_low);

        this.updateThresholdLine(this.context, 'context-target-top', this.settings.bg_target_top, this.yScale2);
        this.updateThresholdLine(this.context, 'context-target-bottom', this.settings.bg_target_bottom, this.yScale2);

        // Update lines
        this.focus.select('.glucose-line')
            .datum(this.data)
            .attr('d', this.line);

        this.context.select('.glucose-line-context')
            .datum(this.data)
            .attr('d', this.line2);

        // Update dots with age-based coloring
        this.updateDots(this.focus, '.dots', this.xScale, this.yScale);
        this.updateDots(this.context, '.dots-context', this.xScale2, this.yScale2, 2);

        // Add "now" line and current reading display
        this.updateNowLine();

        // Set initial brush to show last 3 hours (without triggering events)
        const now = timeExtent[1];
        const threeHoursAgo = new Date(now.getTime() - 3 * 60 * 60 * 1000);

        const brushSelection = [
            this.xScale2(threeHoursAgo),
            this.xScale2(now)
        ];

        this.context.select('.brush').call(this.brush.move, brushSelection);
    }

    updateNowLine() {
        if (this.data.length === 0) return;

        // Get the most recent reading
        const latestReading = this.data[this.data.length - 1];
        const latestTime = new Date(latestReading.date);
        const now = new Date();

        // Check if data is current (within last 15 minutes)
        const ageMinutes = (now - latestTime) / (1000 * 60);
        const isCurrent = ageMinutes < 15;

        // Clear existing now line
        this.nowLineGroup.selectAll('*').remove();

        // Draw vertical "now" line
        const xPos = this.xScale(latestTime);

        this.nowLineGroup.append('line')
            .attr('x1', xPos)
            .attr('y1', 0)
            .attr('x2', xPos)
            .attr('y2', this.height)
            .attr('stroke', isCurrent ? this.colors.nowLine : this.colors.old)
            .attr('stroke-width', 2)
            .attr('opacity', 0.8);

        // Add timestamp label
        const timeFormat = d3.timeFormat('%H:%M');
        this.nowLineGroup.append('text')
            .attr('x', xPos)
            .attr('y', -5)
            .attr('text-anchor', 'middle')
            .attr('fill', isCurrent ? this.colors.nowLine : this.colors.old)
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text(timeFormat(latestTime));

        // Value label removed per user request
    }

    updateDots(container, className, xScale, yScale, radius = 5) {
        const dots = container.select(className)
            .selectAll('circle')
            .data(this.data);

        dots.enter()
            .append('circle')
            .merge(dots)
            .attr('cx', d => xScale(new Date(d.date)))
            .attr('cy', d => yScale(d.sgv))
            .attr('r', radius)
            .attr('fill', d => this.getGlucoseColor(d.sgv))  // Color by value only
            .attr('opacity', 0.9);  // Constant opacity for all dots

        dots.exit().remove();
    }

    updateThresholdLine(container, className, value, yScale = this.yScale) {
        container.select(`.${className}`)
            .attr('x1', 0)
            .attr('y1', yScale(value))
            .attr('x2', this.width)
            .attr('y2', yScale(value));
    }

    brushed(event) {
        if (event.sourceEvent && event.sourceEvent.type === 'zoom') return;
        if (this.isUpdatingFromZoom) return;

        const selection = event.selection;
        if (selection) {
            this.isUpdatingFromBrush = true;

            this.xScale.domain(selection.map(this.xScale2.invert, this.xScale2));
            this.focus.select('.glucose-line').attr('d', this.line);
            this.focus.select('.x-axis').call(this.xAxis);
            this.updateDots(this.focus, '.dots', this.xScale, this.yScale);
            this.updateNowLine();

            // Update display with latest visible data
            if (this.onBrushUpdate) {
                const visibleData = this.data.filter(d => {
                    const time = new Date(d.date);
                    return time >= this.xScale.domain()[0] && time <= this.xScale.domain()[1];
                });
                if (visibleData.length > 0) {
                    const latest = visibleData[visibleData.length - 1];
                    this.onBrushUpdate(latest);
                }
            }

            const transform = d3.zoomIdentity
                .scale(this.width / (selection[1] - selection[0]))
                .translate(-selection[0], 0);
            this.svg.select('.zoom-rect').call(this.zoom.transform, transform);

            this.isUpdatingFromBrush = false;
        }
    }

    zoomed(event) {
        if (event.sourceEvent && event.sourceEvent.type === 'brush') return;
        if (this.isUpdatingFromBrush) return;

        this.isUpdatingFromZoom = true;

        const transform = event.transform;
        this.xScale.domain(transform.rescaleX(this.xScale2).domain());
        this.focus.select('.glucose-line').attr('d', this.line);
        this.focus.select('.x-axis').call(this.xAxis);
        this.updateDots(this.focus, '.dots', this.xScale, this.yScale);
        this.updateNowLine();

        this.context.select('.brush').call(this.brush.move, this.xScale.range().map(transform.invertX, transform));

        this.isUpdatingFromZoom = false;
    }

    getGlucoseColor(sgv) {
        if (sgv >= this.settings.alarm_high) return this.colors.high;
        if (sgv <= this.settings.alarm_low) return this.colors.low;
        if (sgv >= this.settings.bg_target_bottom && sgv <= this.settings.bg_target_top) {
            return this.colors.inRange;
        }
        return this.colors.warning;
    }

    resize() {
        const containerRect = this.container.node().getBoundingClientRect();
        const newWidth = containerRect.width - this.margin.left - this.margin.right;

        if (newWidth !== this.width) {
            this.width = newWidth;
            this.xScale.range([0, this.width]);
            this.xScale2.range([0, this.width]);

            this.svg.select('svg')
                .attr('width', this.width + this.margin.left + this.margin.right);

            if (this.data.length > 0) {
                this.focus.select('.glucose-line').attr('d', this.line);
                this.context.select('.glucose-line-context').attr('d', this.line2);
                this.focus.select('.x-axis').call(this.xAxis);
                this.context.select('.x-axis-context').call(this.xAxis2);
                this.updateDots(this.focus, '.dots', this.xScale, this.yScale);
                this.updateDots(this.context, '.dots-context', this.xScale2, this.yScale2, 2);
                this.updateNowLine();
            }
        }
    }
}
