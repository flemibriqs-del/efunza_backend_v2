# create_favicon.py
import os

favicon_path = '/home/gisbomhj/Efunza/staticfiles/favicon.ico'

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(favicon_path), exist_ok=True)

# Create a simple 1x1 transparent GIF as favicon
gif_data = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

with open(favicon_path, 'wb') as f:
    f.write(gif_data)

print(f"✅ Favicon created at: {favicon_path}")