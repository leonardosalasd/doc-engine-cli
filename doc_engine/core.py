import os
import typst

def build_pdf(input_file: str, output_file: str):
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    try:
        typst.compile(input_file, output=output_file)
    except Exception as e:
        raise RuntimeError(f"Engine compilation failed: {e}")