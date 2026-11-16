"""Technology ecosystem: which skills are asked for together, and which "stacks" that forms.

Method
1. Count how many postings mention both skills (co-occurrence) in a recent window.
2. Turn counts into positive pointwise mutual information (PPMI): high when two skills appear together
   more often than their individual popularity predicts (a plain count would just rank popular skills).
3. Similarity of two skills = cosine of their PPMI rows. Distance = 1 - similarity.
4. Ward hierarchical clustering; k is the best silhouette among the k whose every cluster holds at least
   MIN_CLUSTER skills and at most MAX_SHARE of all skills (plain silhouette alone prefers one giant
   cluster plus tiny outlier clusters).
5. A 2-D map by t-SNE on the same distances (fixed seed, so the picture is reproducible).

Everything is deterministic; clusters describe the recent window and are descriptive, not forecasts.
"""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score

MIN_MENTIONS = 30         # skills mentioned in fewer postings of the window are not clustered
MIN_PAIR = 5              # pair counts below this are treated as noise
MIN_CLUSTER = 5           # a stack with fewer skills is not reported as a cluster
MAX_SHARE = 0.35          # no cluster may hold more than this share of the clustered skills
SEED = 0
K_RANGE = range(4, 9)     # at most 8 clusters: the chart palette has 8 distinguishable hues


def cooccurrence(matrix):
    """Dense co-occurrence counts of a (postings x skills) boolean matrix."""
    product = matrix.astype(np.float32).T @ matrix.astype(np.float32)
    return product.toarray() if hasattr(product, "toarray") else np.asarray(product)


def pair_table(counts, skills, n_postings, min_pair=MIN_PAIR):
    """Pairs (a < b) seen in at least ``min_pair`` postings, with lift = P(a and b) / (P(a) P(b))."""
    n = np.diag(counts).astype(float)
    a, b = np.nonzero(np.triu(counts >= min_pair, k=1))
    lift = counts[a, b] * n_postings / (n[a] * n[b])
    return pd.DataFrame({"a": [skills[i] for i in a], "b": [skills[j] for j in b], "n": counts[a, b].astype(int),
                         "n_a": n[a].astype(int), "n_b": n[b].astype(int), "lift": lift, "window_postings": int(n_postings)})


def ppmi(counts, n_postings, min_pair=MIN_PAIR):
    n = np.diag(counts).astype(float)
    expected = np.outer(n, n) / max(n_postings, 1)
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log(counts / expected)
    pmi[~np.isfinite(pmi)] = 0.0
    pmi[counts < min_pair] = 0.0
    np.fill_diagonal(pmi, 0.0)
    return np.maximum(pmi, 0.0)


def cosine_distance(values):
    norm = np.linalg.norm(values, axis=1, keepdims=True)
    unit = np.divide(values, norm, out=np.zeros_like(values), where=norm > 0)
    dist = np.clip(1.0 - unit @ unit.T, 0.0, 1.0)
    np.fill_diagonal(dist, 0.0)
    return (dist + dist.T) / 2


def layout(dist, seed=SEED):
    """2-D coordinates that keep close skills close (t-SNE on the precomputed distances)."""
    perplexity = float(min(12, max(2, (len(dist) - 1) / 3)))
    return TSNE(n_components=2, metric="precomputed", init="random", perplexity=perplexity, random_state=seed).fit_transform(dist)


def choose_clusters(dist, k_range=K_RANGE, min_size=MIN_CLUSTER, max_share=MAX_SHARE):
    """Ward tree cut at the k with the best silhouette whose clusters all have >= min_size skills and <= max_share of them.

    Returns (labels 1..k, k, silhouette). Falls back to the smallest k in the range if no k satisfies the size rule.
    """
    tree = linkage(squareform(dist, checks=False), method="ward")
    best, fallback = None, None
    for k in k_range:
        if k >= len(dist):
            break
        labels = fcluster(tree, k, criterion="maxclust")
        if len(set(labels)) < 2:
            continue
        score = float(silhouette_score(dist, labels, metric="precomputed"))
        if fallback is None:
            fallback = (labels, k, score)
        sizes = np.bincount(labels)[1:]
        if sizes.min() >= min_size and sizes.max() <= max_share * len(dist) and (best is None or score > best[2]):
            best = (labels, k, score)
    chosen = best or fallback
    if chosen is None:
        raise ValueError("could not form clusters")
    return chosen


def build_clusters(matrix, skills, labels_by_id, min_mentions=MIN_MENTIONS):
    """Cluster the skills of a (postings x skills) boolean matrix.

    Returns (frame, info). ``frame`` has one row per skill: cluster (0 = too few mentions), cluster_name, x, y, mentions.
    """
    counts = cooccurrence(matrix)
    n = np.diag(counts)
    active = np.flatnonzero(n >= min_mentions)
    values = ppmi(counts, matrix.shape[0])[np.ix_(active, active)]
    dist = cosine_distance(values)
    labels, k, silhouette = choose_clusters(dist)
    coords = layout(dist)
    ids = [skills[i] for i in active]
    frame = pd.DataFrame({"skill": ids, "cluster": labels, "x": coords[:, 0], "y": coords[:, 1], "mentions": n[active].astype(int)})
    names = {}
    for c, group in frame.groupby("cluster"):
        top = group.sort_values("mentions", ascending=False).skill.head(3)
        names[c] = " · ".join(labels_by_id[s] for s in top)
    frame["cluster_name"] = frame.cluster.map(names)
    rest = pd.DataFrame({"skill": [skills[i] for i in range(len(skills)) if i not in set(active)]})
    rest = rest.assign(cluster=0, cluster_name="Ít dữ liệu", x=np.nan, y=np.nan, mentions=[int(n[skills.index(s)]) for s in rest.skill])
    return pd.concat([frame, rest], ignore_index=True), {"k": int(k), "silhouette": round(silhouette, 4),
                                                         "clustered_skills": int(len(active)), "window_postings": int(matrix.shape[0])}
