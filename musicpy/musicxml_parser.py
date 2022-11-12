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
                close_tag = False
                if each.endswith('/>'):
                    close_tag = True
                if not close_tag:
                    current_split = each.strip(' ')[1:-1].split(' ', 1)
                else:
                    current_split = each.strip(' ')[1:-2].split(' ', 1)
                current_content = None
                current_attributes = {}
                if len(current_split) == 2:
                    current_type, current_content = current_split
                else:
                    current_type = current_split[0]
                if current_content is not None:
                    current_content = current_content.split('=')
                    new_current_content = []
                    for k in current_content:
                        current_part = k.strip(' ')
                        if current_part.rfind(' ') > current_part.rfind('"'):
                            current_split_ind = current_part.rfind('"')
                            new_current_content.append(
                                current_part[:current_split_ind] + '"')
                            new_current_content.append(
                                current_part[current_split_ind +
                                             1:].strip(' '))
                        else:
                            new_current_content.append(k)
                    current_content = new_current_content
                    current_attributes = {
                        current_content[j]: current_content[j + 1]
                        for j in range(len(current_content)) if j % 2 == 0
                    }
                current_inner_content = current[bracket_inds[i * 2 + 1] +
                                                1:bracket_inds[i * 2 + 2]]
                if current_inner_content.strip('\n ') == '':
                    current_inner_content = None
                current_data = [
                    current_type, current_attributes, current_inner_content
                ]
                if close_tag:
                    body.append(current_data)
                    body.append([current_type, 'end', None])
                    continue
            else:
                current_type = each.strip(' ')[2:-1]
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


def musicxml_to_json(file, output_path, compressed=False):
    result = parse_musicxml(file)
    if not compressed:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result,
                      f,
                      indent=4,
                      separators=(',', ': '),
                      ensure_ascii=False)
    else:
        result = json.dumps(result).encode('utf-8')
        with open(output_path, 'wb') as f:
            f.write(result)
