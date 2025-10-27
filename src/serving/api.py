from fastapi import FastAPI, Request
from pydantic import BaseModel
from src.serving.model_server import ModelServer
from src.features.feature_store import LocalFeatureStore
from src.bidding.bid_strategy import BidStrategyWrapper
import uvicorn


app = FastAPI()

feature_store = LocalFeatureStore(base_path="data/processed")
feature_store.load()

model_server = ModelServer(checkpoint_dir="checkpoints")
strategy = BidStrategyWrapper(
    strategy_type='rl',
    model_dict=model_server.get_all()
)

class BidRequest(BaseModel):
    user_id: str
    adslot_id: str
    request_id: str


# @app.post("/bid")
# async def bid(req: BidRequest):
#     feats = feature_store.get_combined_feature(
#         user_id=req.user_id,
#         adslot_id=req.adslot_id,
#         request_id=req.request_id
#     )
#     if feats is None:
#         return {"bid": 0.0, "reason": "feature not found"}

#     bid_price = strategy.bid(feats)
#     return {"bid": bid_price}

@app.get("/bid")
async def bid_get():
    feats = feature_store.get_combined_feature(
        user_id='u3141',
        adslot_id='s02',
        request_id='req000004'
    )
    if feats is None:
        return {"bid": 0.0, "reason": "feature not found"}

    bid_price = strategy.bid(feats)
    return {"bid": bid_price}

@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("src.serving.api:app", host="0.0.0.0", port=8000, reload=True)
