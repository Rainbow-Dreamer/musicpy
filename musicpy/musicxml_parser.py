import json


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
    length = len(parts)
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
                current_inner_content = current[bracket_inds[i * 2 + 1] +
                                                1:bracket_inds[i * 2 + 2]]
                if current_inner_content.strip('\n ') == '':
                    current_inner_content = None
                current_data = [
                    current_type, current_attributes, current_inner_content
                ]
            else:
                current_type = each[2:-1]
                current_data = [current_type, 'end', None]
            body.append(current_data)
    result_body = parse_inner(body)
    result = {'header': headers, 'body': result_body}
    return result


def parse_inner(current_part):
    result = []
    current_start = None
    current_stop = None
    current_label = None
    current_ind = 0
    for i, each in enumerate(current_part):
        if current_start is None and each[1] != 'end':
            current_start = i
            current_label = each[0]
            current_attributes = each[1]
            if each[2] is not None:
                current_content = each[2]
            else:
                current_content = []
            new_dict = {
                'label': current_label,
                'attributes': current_attributes,
                'content': current_content
            }
            result.append(new_dict)
        else:
            if current_start is not None and each[0] == current_label:
                current_stop = i
                current_label_content = result[current_ind]['content']
                if isinstance(current_label_content, list):
                    current_label_content.extend(
                        parse_inner(current_part[current_start +
                                                 1:current_stop]))
                current_start = None
                current_ind += 1
    return result


def musicxml_to_json(file, output_path):
    result = parse_musicxml(file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result,
                  f,
                  indent=4,
                  separators=(',', ': '),
                  ensure_ascii=False)
