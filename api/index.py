"""
Vercel Serverless Function - Main API Handler
"""
import os
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# In-memory storage for Vercel (serverless - data won't persist between cold starts)
# For production, use a cloud database like Supabase, PlanetScale, or MongoDB Atlas
devices_db = {}
monitors_db = {}

# API Key for agent authentication
API_KEY = os.environ.get('API_KEY', 'default-api-key-change-in-production')


class handler(BaseHTTPRequestHandler):
    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            return json.loads(self.rfile.read(content_length).decode())
        return {}

    def _check_api_key(self):
        api_key = self.headers.get('X-API-Key', '')
        return api_key == API_KEY

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key, Authorization')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Health check
        if path == '/api/health':
            self._send_response(200, {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'version': '1.0.0'
            })
            return

        # Inventory stats
        if path == '/api/inventory/stats':
            total_devices = len(devices_db)
            total_monitors = len(monitors_db)
            online_count = sum(1 for d in devices_db.values() if d.get('status') == 'online')

            self._send_response(200, {
                'total_devices': total_devices,
                'online_devices': online_count,
                'offline_devices': total_devices - online_count,
                'total_monitors': total_monitors,
                'manufacturers': {}
            })
            return

        # List devices
        if path == '/api/devices':
            devices = list(devices_db.values())
            self._send_response(200, {
                'devices': devices,
                'total': len(devices),
                'page': 1,
                'per_page': 50,
                'pages': 1
            })
            return

        # List inventory (same as devices for now)
        if path == '/api/inventory':
            devices = list(devices_db.values())
            self._send_response(200, {
                'inventory': devices,
                'total': len(devices),
                'page': 1,
                'per_page': 50,
                'pages': 1
            })
            return

        # List monitors
        if path == '/api/monitors':
            monitors = list(monitors_db.values())
            self._send_response(200, {
                'monitors': monitors,
                'total': len(monitors),
                'page': 1,
                'per_page': 50,
                'pages': 1
            })
            return

        # Monitor stats
        if path == '/api/monitors/stats':
            self._send_response(200, {
                'total_monitors': len(monitors_db),
                'connected_monitors': len(monitors_db),
                'manufacturers': {},
                'resolutions': {}
            })
            return

        # Get single device
        if path.startswith('/api/devices/') and path != '/api/devices/manufacturers':
            device_id = path.split('/')[-1]
            device = devices_db.get(device_id)
            if device:
                self._send_response(200, device)
            else:
                self._send_response(404, {'error': 'Device not found'})
            return

        # Device manufacturers
        if path == '/api/devices/manufacturers':
            manufacturers = list(set(d.get('manufacturer', 'Unknown') for d in devices_db.values()))
            self._send_response(200, manufacturers)
            return

        # Monitor manufacturers
        if path == '/api/monitors/manufacturers':
            manufacturers = list(set(m.get('manufacturer', 'Unknown') for m in monitors_db.values()))
            self._send_response(200, manufacturers)
            return

        # Users (placeholder)
        if path == '/api/users':
            self._send_response(200, {
                'users': [],
                'total': 0,
                'page': 1,
                'per_page': 50,
                'pages': 0
            })
            return

        self._send_response(404, {'error': 'Not found'})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Receive device data from agent
        if path == '/api/devices':
            if not self._check_api_key():
                self._send_response(401, {'error': 'Invalid API key'})
                return

            data = self._parse_body()
            device_id = data.get('device_id')

            if not device_id:
                self._send_response(400, {'error': 'device_id required'})
                return

            # Store device
            devices_db[device_id] = {
                'id': device_id,
                'hostname': data.get('hostname', 'Unknown'),
                'manufacturer': data.get('system', {}).get('manufacturer', 'Unknown'),
                'model': data.get('system', {}).get('model', 'Unknown'),
                'os_name': data.get('os', {}).get('name', 'Unknown'),
                'os_version': data.get('os', {}).get('version', ''),
                'cpu': data.get('cpu', {}).get('name', 'Unknown'),
                'total_memory_gb': data.get('memory', {}).get('total_gb', 0),
                'status': 'online',
                'last_seen': datetime.now(timezone.utc).isoformat(),
                'created_at': devices_db.get(device_id, {}).get('created_at', datetime.now(timezone.utc).isoformat())
            }

            # Store monitors
            for monitor in data.get('monitors', []):
                monitor_id = monitor.get('monitor_id', monitor.get('id'))
                if monitor_id:
                    monitors_db[monitor_id] = {
                        'id': monitor_id,
                        'device_id': device_id,
                        'manufacturer': monitor.get('manufacturer', 'Unknown'),
                        'model': monitor.get('model', 'Unknown'),
                        'serial_number': monitor.get('serial_number', ''),
                        'native_resolution': f"{monitor.get('native_resolution_x', 0)}x{monitor.get('native_resolution_y', 0)}",
                        'manufacture_year': monitor.get('manufacture_year'),
                        'is_connected': True,
                        'last_seen': datetime.now(timezone.utc).isoformat()
                    }

            self._send_response(200, {
                'message': 'Device data received',
                'device_id': device_id
            })
            return

        self._send_response(404, {'error': 'Not found'})
