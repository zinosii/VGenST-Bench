import cv2
import base64
import re
import ast
import os
import random
import datetime
import time
import importlib
import json
from tqdm import tqdm
import json
import re
import ast

def video_to_base64_frames(video_path, max_frames):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = max(1, total_frames // max_frames)

    frames = []
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        if count % interval == 0:
            _, buffer = cv2.imencode('.jpg', frame)
            b64_str = base64.b64encode(buffer).decode('utf-8')
            frames.append(b64_str)
        count += 1
    cap.release()
    return frames


def fix_json(llm_output_text):
    try:
        if not llm_output_text:
            return None

        text = re.sub(r'```json\s*|\s*```', '', llm_output_text, flags=re.MULTILINE).strip()

        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            text = match.group(1)

        if text.startswith('{{') and text.endswith('}}'):
            text = text[1:-1].strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        try:
            py_text = text.replace("true", "True").replace("false", "False").replace("null", "None")
            return ast.literal_eval(py_text)
        except (ValueError, SyntaxError, TypeError) as e:
            print(f"Parse failed (ast): {e}")
            return None

    except Exception as e:
        print(f"Unexpected fatal error: {e}")
        return None
