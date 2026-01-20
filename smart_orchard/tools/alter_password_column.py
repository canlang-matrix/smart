from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # MySQL 中修改列长度
    try:
        db.session.execute(text("ALTER TABLE users MODIFY password VARCHAR(512);"))
        db.session.commit()
        print('ALTER TABLE executed successfully')
    except Exception as e:
        print('Error executing ALTER TABLE:', e)
        # try alternate syntax
        try:
            db.session.execute(text("ALTER TABLE users MODIFY COLUMN password VARCHAR(512);"))
            db.session.commit()
            print('Alternate ALTER TABLE executed successfully')
        except Exception as e2:
            print('Alternate ALTER TABLE failed:', e2)
