# Block–Layer Prefix Transmission

For each block `k`, let layers `j=0…3` with `0≡not sent`. The atomic transmission unit is a **layer increment** `Δ(k,ℓ)` for `ℓ∈{1,2,3}`, defined as the *minimal* payload to upgrade the block from layer `ℓ-1` to `ℓ`.

**Prefix-decodable:** Any prefix of the stream consisting of `{Δ(k,1)} ∪ {Δ(k,2)} ∪ {Δ(k,3)}` applied in layer order yields a self-consistent map.

**Recommended order:** send all `L1` first; then schedule `L2/L3` by budget-aware utility-density.
