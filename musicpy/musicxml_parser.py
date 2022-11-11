def parse_musicxml(file):
    with open(file, encoding='utf-8') as f:
        current = f.read()
    bracket_inds = [
        i for i, each in enumerate(current) if each == '<' or each == '>'
    ]
    parts = [
        current[bracket_inds[i]:bracket_inds[i + 1] + 1]
        for i in range(len(bracket_inds)) if i % 2 == 0
    ]
    headers = []
    body = []
    for i, each in enumerate(parts):
        if each.startswith('<?') or each.startswith('<!'):
            headers.append(each[1:-1])
        else:
            if not each.startswith('</'):
                current_content = [j for j in each[1:-1].split(' ') if j]
                current_type = current_content[0]
                current_attributes = [
                    j.split('=') for j in current_content[1:]
                ]
                current_attributes = {j[0]: j[1] for j in current_attributes}
                current_data = [current_type, current_attributes]
            else:
                current_type = each[2:-1]
                current_data = [current_type, 'end']
            body.append(current_data)
    print(body)
    result = {}
    result['header'] = headers
