import * as d3 from 'd3';

/**
 * Simple Glucose Chart - No zoom, no brush, just dots and time range buttons
 */
export class SimpleGlucoseChart {
    constructor(containerId) {
        this.container = d3.select(`#${containerId}`);
        this.margin = { top: 40, right: 60, bottom: 60, left: 60 };

        // Nightscout settings
        this.settings = {
            units: 'mg/dL',
            bg_target_top: 180,
            bg_target_bottom: 80,
            alarm_high: 260,
            alarm_low: 55
        };

        // Margins - reserve bottom space for slider (10% of container height)
        const isMobile = window.innerWidth <= 768;
        const containerRect = this.container.node().getBoundingClientRect();
        const bottomMargin = isMobile ? Math.max(containerRect.height * 0.1, 30) : 50;

        this.margin = isMobile
            ? { top: 5, right: 10, bottom: bottomMargin, left: 35 }
            : { top: 20, right: 40, bottom: 50, left: 60 };

        // Colors
        this.colors = {
            background: '#000000',
            gridLines: '#333333',
            axisLabels: '#bdbdbd',
            nowLine: '#0099ff',
            inRange: '#00ff00',
            low: '#ff0000',
            high: '#ffff00',
            urgent: '#ff0000',
            targetRange: 'rgba(0, 255, 0, 0.1)',
            old: '#808080'
        };

        this.data = [];
        this.init();
    }

    init() {
        this.container.selectAll('*').remove();

        // Calculate dimensions
        const containerRect = this.container.node().getBoundingClientRect();
        this.width = containerRect.width - this.margin.left - this.margin.right;

        // Use container height instead of hard-coded values
        this.height = Math.max(containerRect.height - this.margin.top - this.margin.bottom, 150);

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
        this.yScale = d3.scaleLinear().range([this.height, 0]).domain([40, 400]);

        // Axes with proper formatting
        const formatTime = d3.timeFormat('%H:%M');
        this.xAxis = d3.axisBottom(this.xScale)
            .tickFormat(formatTime)
            .ticks(8);

        this.yAxis = d3.axisLeft(this.yScale)
            .tickFormat(d3.format('d'))
            .tickValues([40, 55, 80, 120, 180, 260, 400]);

        // Improve x-axis styling for better visibility on mobile
        const isMobile = window.innerWidth <= 768;

        // Add grid
        this.svg.append('g')
            .attr('class', 'grid')
            .attr('transform', `translate(0,${this.height})`)
            .style('color', this.colors.gridLines)
            .style('stroke-dasharray', '2,2');

        // Add target range background
        this.svg.append('rect')
            .attr('class', 'target-range')
            .attr('fill', this.colors.targetRange)
            .attr('x', 0)
            .attr('width', this.width);

        // Add threshold lines
        this.addThresholdLine('high-line', this.settings.alarm_high, this.colors.high);
        this.addThresholdLine('target-top-line', this.settings.bg_target_top, this.colors.inRange);
        this.addThresholdLine('target-bottom-line', this.settings.bg_target_bottom, this.colors.inRange);
        this.addThresholdLine('low-line', this.settings.alarm_low, this.colors.low);

        // Add dots container
        this.svg.append('g').attr('class', 'dots');

        // Add axes
        this.svg.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${this.height})`)
            .style('color', this.colors.axisLabels)
            .style('font-size', isMobile ? '12px' : '11px')
            .style('font-weight', '600');

        this.svg.append('g')
            .attr('class', 'y-axis')
            .style('color', this.colors.axisLabels)
            .style('font-size', isMobile ? '12px' : '11px')
            .style('font-weight', '600');

        // Axis labels removed for cleaner mobile view

        // Add "now" line group
        this.nowLineGroup = this.svg.append('g').attr('class', 'now-line-group');
    }

    addThresholdLine(className, value, color) {
        this.svg.append('line')
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
        this.xScale.domain(timeExtent);

        // Update axes
        this.svg.select('.x-axis').call(this.xAxis);
        this.svg.select('.y-axis').call(this.yAxis);

        // Update target range
        this.svg.select('.target-range')
            .attr('y', this.yScale(this.settings.bg_target_top))
            .attr('height', this.yScale(this.settings.bg_target_bottom) - this.yScale(this.settings.bg_target_top));

        // Update threshold lines
        this.updateThresholdLine('high-line', this.settings.alarm_high);
        this.updateThresholdLine('target-top-line', this.settings.bg_target_top);
        this.updateThresholdLine('target-bottom-line', this.settings.bg_target_bottom);
        this.updateThresholdLine('low-line', this.settings.alarm_low);

        // Update dots
        this.updateDots();

        // Update "now" line
        this.updateNowLine();
    }

    updateThresholdLine(className, value) {
        this.svg.select(`.${className}`)
            .attr('x1', 0)
            .attr('y1', this.yScale(value))
            .attr('x2', this.width)
            .attr('y2', this.yScale(value));
    }

    updateDots() {
        const dots = this.svg.select('.dots')
            .selectAll('circle')
            .data(this.data);

        dots.enter()
            .append('circle')
            .merge(dots)
            .attr('cx', d => this.xScale(new Date(d.date)))
            .attr('cy', d => this.yScale(d.sgv))
            .attr('r', 5)
            .attr('fill', d => this.getGlucoseColor(d.sgv))
            .attr('opacity', 0.9);

        dots.exit().remove();
    }

    updateNowLine() {
        if (this.data.length === 0) return;

        const latestReading = this.data[this.data.length - 1];
        const latestTime = new Date(latestReading.date);
        const now = Date.now();
        const ageMinutes = (now - latestTime) / (1000 * 60);
        const isCurrent = ageMinutes < 15;

        this.nowLineGroup.selectAll('*').remove();

        const xPos = this.xScale(latestTime);

        // Draw vertical line
        this.nowLineGroup.append('line')
            .attr('class', 'now-line-vertical')
            .attr('x1', xPos)
            .attr('y1', 0)
            .attr('x2', xPos)
            .attr('y2', this.height)
            .attr('stroke', isCurrent ? this.colors.nowLine : this.colors.old)
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', '5,5')
            .attr('opacity', 0.8);

        // Add timestamp label at top
        const timeFormat = d3.timeFormat('%H:%M');
        this.nowLineGroup.append('text')
            .attr('x', xPos)
            .attr('y', -10)
            .attr('text-anchor', 'middle')
            .attr('fill', isCurrent ? this.colors.nowLine : this.colors.old)
            .attr('font-size', '12px')
            .attr('font-weight', 'bold')
            .text(timeFormat(latestTime));

        // Add draggable handle at the bottom
        const handleGroup = this.nowLineGroup.append('g')
            .attr('class', 'drag-handle')
            .attr('cursor', 'ew-resize');

        // Handle background circle
        handleGroup.append('circle')
            .attr('cx', xPos)
            .attr('cy', this.height)
            .attr('r', 12)
            .attr('fill', isCurrent ? this.colors.nowLine : this.colors.old)
            .attr('opacity', 0.8);

        // Handle icon (vertical lines)
        handleGroup.append('line')
            .attr('x1', xPos - 3)
            .attr('y1', this.height - 6)
            .attr('x2', xPos - 3)
            .attr('y2', this.height + 6)
            .attr('stroke', '#ffffff')
            .attr('stroke-width', 2);

        handleGroup.append('line')
            .attr('x1', xPos + 3)
            .attr('y1', this.height - 6)
            .attr('x2', xPos + 3)
            .attr('y2', this.height + 6)
            .attr('stroke', '#ffffff')
            .attr('stroke-width', 2);

        // Add drag behavior
        const drag = d3.drag()
            .on('drag', (event) => {
                const newX = Math.max(0, Math.min(this.width, event.x));
                const newTime = this.xScale.invert(newX);

                // Find closest data point
                const closestData = this.data.reduce((prev, curr) => {
                    const prevDiff = Math.abs(new Date(prev.date) - newTime);
                    const currDiff = Math.abs(new Date(curr.date) - newTime);
                    return currDiff < prevDiff ? curr : prev;
                });

                // Update line position
                this.nowLineGroup.select('.now-line-vertical')
                    .attr('x1', newX)
                    .attr('x2', newX);

                // Update timestamp
                this.nowLineGroup.select('text')
                    .attr('x', newX)
                    .text(timeFormat(new Date(closestData.date)));

                // Update handle position
                handleGroup.selectAll('circle, line')
                    .attr('cx', newX)
                    .attr('x1', (d, i) => i === 0 ? newX - 3 : newX + 3)
                    .attr('x2', (d, i) => i === 0 ? newX - 3 : newX + 3);

                // Callback to update stat cards if provided
                if (this.onNowLineDrag) {
                    this.onNowLineDrag(closestData);
                }
            });

        handleGroup.call(drag);
    }

    getGlucoseColor(value) {
        if (value < this.settings.alarm_low) return this.colors.low;
        if (value < this.settings.bg_target_bottom) return this.colors.high;
        if (value <= this.settings.bg_target_top) return this.colors.inRange;
        if (value <= this.settings.alarm_high) return this.colors.high;
        return this.colors.urgent;
    }

    resize() {
        this.init();
        if (this.data.length > 0) {
            this.updateData(this.data);
        }
    }

    /**
     * Add a new entry in real-time (from WebSocket)
     */
    addEntry(entry) {
        if (!entry || !entry.date) return;

        // Add to data array
        this.data.push(entry);

        // Sort by date
        this.data.sort((a, b) => new Date(a.date) - new Date(b.date));

        // Update the chart
        this.updateData(this.data);

        console.log('[Chart] Added new entry:', entry);
    }
}
