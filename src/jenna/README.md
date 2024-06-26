# Jenna Folder Breakdown

**Data Download:**
download joined data from WRDS with WRDS connection

**Phase 1:**
the model learns embeddings one stock at a time, and then clustering the stocks using the trained embeddings

**Phase 2:**
doing the same thing, but with added datasets (Compustat, etc.) + sector/market/cluster weighted average, then generate embedding

**Phase 3:**
feed neighbors/offsets, WITH the actual future return/vol of these neighbors/offsets) + together with the stock to predict return (to generate embeddings)
