import os


def extract_images(document, image_dir):
    rels = document.part.rels
    image_map = {}

    for rel_id, rel in rels.items():
        if "image" in rel.target_ref:
            image_data = rel.target_part.blob
            content_type = rel.target_part.content_type
            ext = content_type.split('/')[-1]
            if ext == 'jpeg':
                ext = 'jpg'
            elif ext not in ['png', 'jpg', 'gif', 'pdf']:
                ext = 'png'

            filename = f"img_{rel_id.replace('rId', '')}.{ext}"
            filepath = os.path.join(image_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            image_map[rel_id] = filepath

    return image_map


def get_image_rel_ids(paragraph):
    rel_ids = []
    blips = paragraph._element.xpath('.//a:blip/@r:embed')
    for blip in blips:
        rel_ids.append(blip)
    return rel_ids
