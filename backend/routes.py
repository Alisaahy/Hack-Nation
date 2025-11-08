from fastapi import APIRouter

# Create a router for organizing your API routes
router = APIRouter()

@router.get("/example")
async def example_endpoint():
    """
    Example API endpoint.
    Add your own routes here!
    """
    return {"message": "This is an example endpoint", "status": "success"}

