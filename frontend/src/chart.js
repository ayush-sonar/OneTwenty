import * as d3 from 'd3';

export class GlucoseChart {
    constructor(containerId, settings) {
        this.container = d3.select(`#${containerId}`);
        this.settings = settings || {
            units: 'mg/dl',
            bg_target_top: 180,
            bg_target_bottom: 80,
            alarm_high: 260,
            alarm_low: 70
        };

        this.margin = { top: 20, right: 50, bottom: 30, left: 50 };
        this.data = [];
    }

    init() {
        // Clear any existing chart
        this.container.selectAll('*').remove();

        // Get container dimensions
        const containerRect = this.container.node().getBoundingClientRect();
        this.width = containerRect.width - this.margin.left - this.margin.right;
        this.height = 400 - this.margin.top - this.margin.bottom;

        // Create SVG
        this.svg = this.container
            .append('svg')
            .attr('width', this.width + this.margin.left + this.margin.right)
            .attr('height', this.height + this.margin.top + this.margin.bottom)
            .append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Create scales
        this.xScale = d3.scaleTime().range([0, this.width]);
        this.yScale = d3.scaleLinear().range([this.height, 0]);

        // Create axes
        this.xAxis = d3.axisBottom(this.xScale).ticks(6);
        this.yAxis = d3.axisLeft(this.yScale).ticks(8);

        // Append axes
        this.svg.append('g')
            .attr('class', 'x-axis')
            .attr('transform', `translate(0,${this.height})`)
            .style('color', '#a0a0a0');

        this.svg.append('g')
            .attr('class', 'y-axis')
            .style('color', '#a0a0a0');

        // Add target range area
        this.svg.append('rect')
            .attr('class', 'target-range')
            .attr('fill', 'rgba(46, 204, 113, 0.1)');

        // Add threshold lines
        this.addThresholdLine('high-line', this.settings.alarm_high, '#e74c3c');
        this.addThresholdLine('target-top-line', this.settings.bg_target_top, '#2ecc71');
        this.addThresholdLine('target-bottom-line', this.settings.bg_target_bottom, '#2ecc71');
        this.addThresholdLine('low-line', this.settings.alarm_low, '#e74c3c');

        // Create line generator
        this.line = d3.line()
            .x(d => this.xScale(new Date(d.date)))
            .y(d => this.yScale(d.sgv))
            .curve(d3.curveMonotoneX);

        // Add path for glucose line
        this.svg.append('path')
            .attr('class', 'glucose-line')
            .attr('fill', 'none')
            .attr('stroke', '#3498db')
            .attr('stroke-width', 2);

        // Add dots group
        this.svg.append('g').attr('class', 'dots');
    }

    addThresholdLine(className, value, color) {
        this.svg.append('line')
            .attr('class', className)
            .attr('stroke', color)
            .attr('stroke-width', 1)
            .attr('stroke-dasharray', '5,5')
            .attr('opacity', 0.6);
    }

    updateData(entries) {
        if (!entries || entries.length === 0) return;

        this.data = entries.sort((a, b) => new Date(a.date) - new Date(b.date));

        // Update scales
        const timeExtent = d3.extent(this.data, d => new Date(d.date));
        const glucoseExtent = d3.extent(this.data, d => d.sgv);

        this.xScale.domain(timeExtent);
        this.yScale.domain([
            Math.min(this.settings.alarm_low - 20, glucoseExtent[0]),
            Math.max(this.settings.alarm_high + 20, glucoseExtent[1])
        ]);

        // Update axes
        this.svg.select('.x-axis').call(this.xAxis);
        this.svg.select('.y-axis').call(this.yAxis);

        // Update target range
        this.svg.select('.target-range')
            .attr('x', 0)
            .attr('y', this.yScale(this.settings.bg_target_top))
            .attr('width', this.width)
            .attr('height', this.yScale(this.settings.bg_target_bottom) - this.yScale(this.settings.bg_target_top));

        // Update threshold lines
        this.updateThresholdLine('high-line', this.settings.alarm_high);
        this.updateThresholdLine('target-top-line', this.settings.bg_target_top);
        this.updateThresholdLine('target-bottom-line', this.settings.bg_target_bottom);
        this.updateThresholdLine('low-line', this.settings.alarm_low);

        // Update glucose line
        this.svg.select('.glucose-line')
            .datum(this.data)
            .attr('d', this.line);

        // Update dots
        const dots = this.svg.select('.dots')
            .selectAll('circle')
            .data(this.data);

        dots.enter()
            .append('circle')
            .merge(dots)
            .attr('cx', d => this.xScale(new Date(d.date)))
            .attr('cy', d => this.yScale(d.sgv))
            .attr('r', 4)
            .attr('fill', d => this.getGlucoseColor(d.sgv))
            .attr('opacity', 0.8);

        dots.exit().remove();
    }

    updateThresholdLine(className, value) {
        this.svg.select(`.${className}`)
            .attr('x1', 0)
            .attr('y1', this.yScale(value))
            .attr('x2', this.width)
            .attr('y2', this.yScale(value));
    }

    getGlucoseColor(sgv) {
        if (sgv >= this.settings.alarm_high) return '#e74c3c';
        if (sgv <= this.settings.alarm_low) return '#e74c3c';
        if (sgv >= this.settings.bg_target_bottom && sgv <= this.settings.bg_target_top) {
            return '#2ecc71';
        }
        return '#f39c12';
    }

    resize() {
        const containerRect = this.container.node().getBoundingClientRect();
        const newWidth = containerRect.width - this.margin.left - this.margin.right;

        if (newWidth !== this.width) {
            this.width = newWidth;
            this.xScale.range([0, this.width]);

            this.svg.select('svg')
                .attr('width', this.width + this.margin.left + this.margin.right);

            if (this.data.length > 0) {
                this.updateData(this.data);
            }
        }
    }
}
