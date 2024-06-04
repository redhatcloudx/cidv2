import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Image, Base

engine = create_engine('postgresql://postgres:postgres@db:5432/test_db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def load_data(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def import_data(images):
    session = Session()
    for image in images:
        image_obj = Image(
            name=image.get('name'),
            arch=image.get('arch'),
            version=image.get('version'),
            imageId=image.get('imageId'),
            date=image.get('date'),
            virt=image.get('virt'),
            provider=image.get('provider'),
            region=image.get('region')
        )
        session.add(image_obj)
    session.commit()

if __name__ == "__main__":
    images = load_data('data.json')
    import_data(images)
