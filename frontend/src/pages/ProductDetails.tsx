import { useParams } from "react-router-dom";
import "./ProductDetails.css";



function ProductDetails() {
    const { id } = useParams();

    return (
        <div className="product-details-container">
            <h1>Product Details</h1>
            <p>Details for product with ID: {id}</p>
        </div>
    )
}

export default ProductDetails;