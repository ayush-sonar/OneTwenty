/**
 * Adapter layer to bridge Python FastAPI backend with Nightscout client
 * Maps Python API responses to the format expected by the original Nightscout client
 */

import api from './api.js';

export class NightscoutAdapter {
    constructor() {
        this.baseURL = 'http://localhost:8000/api/v1';
    }

    /**
     * Get status/settings from Python backend and format for Nightscout client
     */
    async getStatus() {
        const status = await api.getStatus();

        // Map Python API response to Nightscout format
        return {
            status: 'ok',
            name: status.name || 'Nightscout',
            version: '15.0.0-saas',
            serverTime: new Date().toISOString(),
            serverTimeEpoch: Date.now(),
            apiEnabled: true,
            careportalEnabled: true,
            boluscalcEnabled: true,
            head: 'main',
            settings: {
                units: status.units || 'mg/dl',
                timeFormat: 24,
                nightMode: false,
                editMode: true,
                showRawbg: 'never',
                customTitle: status.name || 'Nightscout',
                theme: 'colors',
                alarmUrgentHigh: true,
                alarmHigh: true,
                alarmLow: true,
                alarmUrgentLow: true,
                alarmTimeagoWarn: true,
                alarmTimeagoWarnMins: 15,
                alarmTimeagoUrgent: true,
                alarmTimeagoUrgentMins: 30,
                language: 'en',
                scaleY: 'log',
                showPlugins: '',
                showForecast: 'ar2',
                focusHours: 3,
                heartbeat: 60,
                baseURL: this.baseURL,
                authDefaultRoles: 'readable',
                thresholds: {
                    bgHigh: status.thresholds?.bg_high || 260,
                    bgTargetTop: status.thresholds?.bg_target_top || 180,
                    bgTargetBottom: status.thresholds?.bg_target_bottom || 80,
                    bgLow: status.thresholds?.bg_low || 70
                },
                DEFAULT_FEATURES: [
                    'bgnow',
                    'delta',
                    'direction',
                    'timeago',
                    'devicestatus',
                    'upbat',
                    'errorcodes',
                    'profile',
                    'dbsize'
                ],
                alarmTypes: ['simple'],
                enable: status.enable || []
            },
            extendedSettings: {
                devicestatus: {
                    advanced: true
                }
            },
            authorized: null,
            runtimeState: 'loaded'
        };
    }

    /**
     * Get entries from Python backend
     */
    async getEntries(count = 288) {
        return await api.getEntries(count);
    }

    /**
     * Get treatments - stub for now
     */
    async getTreatments() {
        // TODO: Implement when backend endpoint is ready
        return [];
    }

    /**
     * Get profile - stub for now
     */
    async getProfile() {
        // TODO: Implement when backend endpoint is ready
        return [{
            defaultProfile: 'Default',
            store: {
                'Default': {
                    dia: 3,
                    carbratio: [{
                        time: '00:00',
                        value: 10
                    }],
                    sens: [{
                        time: '00:00',
                        value: 50
                    }],
                    basal: [{
                        time: '00:00',
                        value: 1.0
                    }],
                    target_low: [{
                        time: '00:00',
                        value: 80
                    }],
                    target_high: [{
                        time: '00:00',
                        value: 180
                    }],
                    units: 'mg/dl'
                }
            },
            startDate: new Date().toISOString(),
            mills: Date.now()
        }];
    }

    /**
     * Get device status - stub for now
     */
    async getDeviceStatus() {
        // TODO: Implement when backend endpoint is ready
        return [];
    }

    /**
     * Create a mock Socket.IO interface for real-time updates
     * For now, we'll use polling
     */
    createSocketStub() {
        return {
            on: (event, callback) => {
                console.log(`Socket event registered: ${event}`);
                // Could implement polling here later
            },
            emit: (event, data) => {
                console.log(`Socket emit: ${event}`, data);
            },
            off: (event) => {
                console.log(`Socket event unregistered: ${event}`);
            }
        };
    }
}

export default new NightscoutAdapter();
