def save_html(html_str, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_str)
