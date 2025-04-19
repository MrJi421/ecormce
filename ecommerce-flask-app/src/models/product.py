class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Product {self.name}>'

    @classmethod
    def create(cls, name, description, price):
        new_product = cls(name=name, description=description, price=price)
        db.session.add(new_product)
        db.session.commit()
        return new_product

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def get_by_id(cls, product_id):
        return cls.query.get(product_id)

    @classmethod
    def update(cls, product_id, name=None, description=None, price=None):
        product = cls.query.get(product_id)
        if product:
            if name is not None:
                product.name = name
            if description is not None:
                product.description = description
            if price is not None:
                product.price = price
            db.session.commit()
        return product

    @classmethod
    def delete(cls, product_id):
        product = cls.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
        return product