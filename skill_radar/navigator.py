"""Skill Navigator: how many postings fit the skills I already have, and which skill should I learn next?

A posting FITS a person when they know at least ``threshold`` of the skills the posting mentions
(for example 50% of its detected skills). Postings without any detected skill are ignored.

The next-skill advice is greedy: the skill that turns the most not-yet-fitting postings into fitting
ones is added first, then the process repeats. This is descriptive of the Hacker News postings only.
"""

import numpy as np

TOLERANCE = 1e-9


def dense_matrix(posting, posting_skill, skills):
    """Boolean (postings x skills) matrix; only postings with at least one detected skill are kept.

    Returns (matrix, kept_posting_index) where kept_posting_index are row positions in ``posting``.
    """
    row = {pid: i for i, pid in enumerate(posting.pid)}
    col = {s: j for j, s in enumerate(skills)}
    matrix = np.zeros((len(posting), len(skills)), dtype=bool)
    rows = posting_skill.pid.map(row)
    cols = posting_skill.skill.map(col)
    ok = rows.notna() & cols.notna()
    matrix[rows[ok].astype(int).to_numpy(), cols[ok].astype(int).to_numpy()] = True
    keep = np.flatnonzero(matrix.any(axis=1))
    return matrix[keep], keep


def fits(matrix, known, threshold):
    """Boolean per posting: does the person know >= threshold of the posting's skills?"""
    if not len(known):
        return np.zeros(len(matrix), dtype=bool)
    needed = matrix.sum(axis=1)
    have = matrix[:, known].sum(axis=1)
    return have >= threshold * needed - TOLERANCE


def coverage(matrix, known, threshold):
    if not len(matrix):
        return 0.0
    return float(fits(matrix, known, threshold).mean())


def gains(matrix, known, threshold):
    """For each skill: postings that would start to fit if it were learned (0 for skills already known)."""
    needed = matrix.sum(axis=1)
    have = matrix[:, known].sum(axis=1) if len(known) else np.zeros(len(matrix))
    fitting = have >= threshold * needed - TOLERANCE if len(known) else np.zeros(len(matrix), dtype=bool)
    out = np.zeros(matrix.shape[1], dtype=int)
    for j in range(matrix.shape[1]):
        if j in set(known):
            continue
        rows = matrix[:, j] & ~fitting
        out[j] = int((have[rows] + 1 >= threshold * needed[rows] - TOLERANCE).sum())
    return out


def plan(matrix, known, threshold, steps=5):
    """Greedy learning path: list of dicts (skill index, extra postings, coverage after each step)."""
    known = list(known)
    path = []
    for _ in range(steps):
        g = gains(matrix, known, threshold)
        j = int(g.argmax())
        if g[j] <= 0:
            break
        known.append(j)
        path.append({"skill": j, "gain": int(g[j]), "coverage": coverage(matrix, known, threshold)})
    return path
