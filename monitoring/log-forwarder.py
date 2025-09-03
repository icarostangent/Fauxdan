#!/usr/bin/env python3
"""
Simple log forwarder that tails Django log files and sends them to Logstash via TCP
"""
import json
import socket
import time
import os
import sys
from pathlib import Path

def send_log_to_logstash(log_entry, logstash_host='logstash', logstash_port=5000):
    """Send a log entry to Logstash via TCP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((logstash_host, logstash_port))
        sock.send((json.dumps(log_entry) + '\n').encode('utf-8'))
        sock.close()
        return True
    except Exception as e:
        print(f"Error sending log to Logstash: {e}", file=sys.stderr)
        return False

def tail_log_file(file_path, logstash_host='logstash', logstash_port=5000):
    """Tail a log file and forward entries to Logstash"""
    print(f"Starting to tail {file_path}")
    
    # Get the initial file size
    if not os.path.exists(file_path):
        print(f"Log file {file_path} does not exist yet, waiting...")
        while not os.path.exists(file_path):
            time.sleep(1)
    
    with open(file_path, 'r') as f:
        # Go to end of file
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            
            try:
                # Parse the JSON log entry
                log_entry = json.loads(line.strip())
                
                # Add container/service identification
                log_entry['container'] = 'backend'
                log_entry['service'] = log_entry.get('logger', 'django')
                
                # Send to Logstash
                if send_log_to_logstash(log_entry, logstash_host, logstash_port):
                    print(f"Forwarded log: {log_entry.get('level', 'INFO')} - {log_entry.get('message', '')[:50]}...")
                
            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue
            except Exception as e:
                print(f"Error processing log line: {e}", file=sys.stderr)
                continue

if __name__ == "__main__":
    # Get log file path from environment or use default
    log_file = os.environ.get('LOG_FILE', '/var/log/app/django.log')
    
    # Get Logstash connection details
    logstash_host = os.environ.get('LOGSTASH_HOST', 'logstash')
    logstash_port = int(os.environ.get('LOGSTASH_PORT', '5000'))
    
    print(f"Starting log forwarder for {log_file} -> {logstash_host}:{logstash_port}")
    
    try:
        tail_log_file(log_file, logstash_host, logstash_port)
    except KeyboardInterrupt:
        print("Log forwarder stopped")
    except Exception as e:
        print(f"Log forwarder error: {e}", file=sys.stderr)
        sys.exit(1)
