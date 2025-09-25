from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api, reqparse, fields, marshal_with, abort
from flask import request
from datetime import datetime,date
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/mobilepointofsale'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
api = Api(app)

class ProductModel(db.Model):

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)  
    description = db.Column(db.String(80),  nullable = False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    


    def __repr__(self):
        return f"<Product {self.name}>"
    
class SaleModel(db.Model):
    
    id = db.Column(db.Integer,primary_key=True)
    product_id = db.Column(db.Integer,db.ForeignKey('product_model.id'), nullable= False)
    quantity= db.Column(db.Integer,nullable=False)
    total_amount = db.Column(db.Float, nullable= False)
    tax=db.Column(db.Float,default=0.0)
    
   
    product= db.relationship('ProductModel', backref=db.backref('sales',lazy=True))

    def __repr__(self):
        return f"<Sale Product-{self.prodcut.name} Qty={self.quantity}>"



product_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'price' : fields.Float,
    'stock' : fields.Integer,
    
}

sale_fields={
    'id': fields.Integer,
    'product_id' : fields.Integer,
    'quantity': fields.Integer,
    'total_amount': fields.Float,
    'tax': fields.Float,
    
}


class Products(Resource):
    @marshal_with(product_fields)
    def get(self):
        return  ProductModel.query.all()
    
    @marshal_with(product_fields)
    def post(self):
        data = request.get_json()
        new_product = ProductModel(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            stock=data.get('stock', 0)
        )
        db.session.add(new_product)
        db.session.commit()
        return new_product, 201
    
    #CRUD END POINTS
class Product(Resource):
    @marshal_with(product_fields)
    def get(self, product_id):
        product = ProductModel.query.get(product_id)
        if not product:
            return {"message": "Product not found"}, 404
        return product

    @marshal_with(product_fields)
    def patch(self, product_id):
        product = ProductModel.query.get(product_id)
        if not product:
            return {"message": "Product not found"}, 404

        data = request.get_json()
        if "name" in data:
            product.name = data["name"]
        if "description" in data:
            product.description = data["description"]
        if "price" in data:
            product.price = data["price"]
        if "stock" in data:
            product.stock = data["stock"]

        db.session.commit()
        return product

    def delete(self, product_id):
        product = ProductModel.query.get(product_id)
        if not product:
            return {"message": "Product not found"}, 404

        db.session.delete(product)
        db.session.commit()
        return {"message": "Product deleted successfully"}, 200
    
    
class Sales(Resource):
    @marshal_with(sale_fields)
    def get(self):
        return SaleModel.query.all()
    
    @marshal_with(sale_fields)
    def post(self):
        data = request.get_json()
        new_sale = SaleModel(
            product_id=data['product_id'],
            quantity=data['quantity'],
            total_amount=data['total_amount'],
            tax=data.get('tax', 0.0)
        )
        db.session.add(new_sale)
        db.session.commit()
        return {
            'id': new_sale.id,
            'product_id': new_sale.product_id,
            'quantity': new_sale.quantity,
            'total_amount': new_sale.total_amount,
            'tax': new_sale.tax
        }, 201
    
class ProductSalesReport(Resource):
    def get(self):
        sales = SaleModel.query.all()
        report = {}
        for s in sales:
            product_name = s.product.name
            if product_name not in report:
                report[product_name] = {"quantity": 0, "total_amount": 0.0, "tax": 0.0}
            report[product_name]["quantity"] += s.quantity
            report[product_name]["total_amount"] += s.total_amount
            report[product_name]["tax"] += s.tax
        return report
    
class DailySalesReport(Resource):
    def get(self):
        today = date.today()
        sales_today = SaleModel.query.filter(func.date(SaleModel.created_at) == today).all()

        total_sales = sum(s.total_amount for s in sales_today)
        total_tax = sum(s.tax for s in sales_today)
        total_transactions = len(sales_today)

        return {
            "date": str(today),
            "total_sales": total_sales,
            "total_tax": total_tax,
            "total_transactions": total_transactions
        }


        
   
   
api.add_resource(Products, '/api/products/')
api.add_resource(Product, '/api/products/<int:product_id>')
api.add_resource(Sales, '/api/sales/')
api.add_resource(ProductSalesReport,'/api/reports/products')
api.add_resource(DailySalesReport, '/api/reports/daily-sales')

@app.route('/')
def home():
    return '<h1> Flask rest API for Products and Sales Reporting</h1>'

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug = True)