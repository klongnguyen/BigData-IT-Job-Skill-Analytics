"""Skill taxonomy for the Skill Radar project.

One entry per technology, with three things:
  * ``aliases``  how the skill is written in free-text job postings;
  * ``category`` coarse family used by the dashboard;
  * signal mappings (``se_tag`` Stack Overflow tag, ``npm`` package, ``gh`` GitHub language)
    used as *leading indicators* of demand.

Alias syntax: a plain string is matched case-insensitively on whole tokens; ``re:`` is a raw
case-insensitive regex; ``cs:`` is a raw case-sensitive regex (for words that are also normal
English, such as "Go" and "Swift").
"""

import html
import re
from functools import lru_cache

W = r"(?<![\w.#+])"          # not preceded by a word character, dot, # or +
E = r"(?![\w#+])"            # not followed by a word character, # or +

SKILLS = [
    # ---- languages
    dict(id="python", label="Python", category="language", aliases=["python", "python3"], se_tag="python", gh="Python"),
    dict(id="javascript", label="JavaScript", category="language",
         aliases=["javascript", "ecmascript", r"re:(?<![\w.])js(?!\w)(?!\.\w)"], se_tag="javascript", gh="JavaScript"),
    dict(id="typescript", label="TypeScript", category="language", aliases=["typescript"], se_tag="typescript", npm="typescript", gh="TypeScript"),
    dict(id="java", label="Java", category="language", aliases=[r"re:(?<![\w.])java(?![\w#])(?!\.\w)"], se_tag="java", gh="Java"),
    dict(id="cpp", label="C++", category="language", aliases=["c++", "cpp"], se_tag="c++", gh="C++"),
    dict(id="csharp", label="C#", category="language", aliases=["c#", "csharp"], se_tag="c#", gh="C#"),
    dict(id="go", label="Go", category="language",
         aliases=["golang", r"cs:(?<![\w.])Go(?![\w-])(?!\.\w)(?!\s+(?:to|for|with|from|beyond|further|live|ahead|forward|through|on|get|out|team|market|big|above))"],
         se_tag="go", gh="Go"),
    dict(id="rust", label="Rust", category="language", aliases=["rust", "rustlang"], gh="Rust", se_tag="rust"),
    dict(id="ruby", label="Ruby", category="language", aliases=["ruby"], se_tag="ruby", gh="Ruby"),
    dict(id="php", label="PHP", category="language", aliases=["php"], se_tag="php", gh="PHP"),
    dict(id="swift", label="Swift", category="language", aliases=[r"cs:(?<![\w.])Swift(?!\w)(?!\.\w)"], se_tag="swift", gh="Swift"),
    dict(id="kotlin", label="Kotlin", category="language", aliases=["kotlin"], se_tag="kotlin", gh="Kotlin"),
    dict(id="scala", label="Scala", category="language", aliases=["scala"], se_tag="scala", gh="Scala"),
    dict(id="elixir", label="Elixir", category="language", aliases=["elixir"], se_tag="elixir", gh="Elixir"),
    dict(id="clojure", label="Clojure", category="language", aliases=["clojure", "clojurescript"], se_tag="clojure", gh="Clojure"),
    dict(id="haskell", label="Haskell", category="language", aliases=["haskell"], se_tag="haskell", gh="Haskell"),
    dict(id="erlang", label="Erlang", category="language", aliases=["erlang"], gh="Erlang"),
    dict(id="perl", label="Perl", category="language", aliases=["perl"], gh="Perl"),
    dict(id="objc", label="Objective-C", category="language", aliases=["objective-c", "objective c", "objc"], gh="Objective-C"),
    dict(id="sql", label="SQL", category="language", aliases=["sql"], se_tag="sql"),
    # ---- front end
    dict(id="react", label="React", category="frontend", aliases=[r"re:(?<![\w.])react(?:\.?js)?(?![\w-])(?!\s+native)"], se_tag="reactjs", npm="react"),
    dict(id="angular", label="Angular", category="frontend", aliases=["angular", "angularjs", "angular.js"], se_tag="angular", npm="@angular/core"),
    dict(id="vue", label="Vue", category="frontend", aliases=["vue", "vue.js", "vuejs"], se_tag="vue.js", npm="vue"),
    dict(id="jquery", label="jQuery", category="frontend", aliases=["jquery"], se_tag="jquery", npm="jquery"),
    dict(id="svelte", label="Svelte", category="frontend", aliases=["svelte", "sveltekit"], se_tag="svelte", npm="svelte"),
    dict(id="nextjs", label="Next.js", category="frontend", aliases=["next.js", "nextjs"], se_tag="next.js", npm="next"),
    dict(id="graphql", label="GraphQL", category="frontend", aliases=["graphql"], se_tag="graphql", npm="graphql"),
    dict(id="webassembly", label="WebAssembly", category="frontend", aliases=["webassembly", "wasm"], se_tag="webassembly"),
    dict(id="tailwind", label="Tailwind CSS", category="frontend", aliases=["tailwind", "tailwindcss"], npm="tailwindcss"),
    # ---- back end
    dict(id="node", label="Node.js", category="backend", aliases=["node.js", "nodejs"], se_tag="node.js"),
    dict(id="rails", label="Ruby on Rails", category="backend", aliases=["ruby on rails", "rails"], se_tag="ruby-on-rails"),
    dict(id="django", label="Django", category="backend", aliases=["django"], se_tag="django"),
    dict(id="flask", label="Flask", category="backend", aliases=["flask"], se_tag="flask"),
    dict(id="spring", label="Spring", category="backend", aliases=["spring boot", "spring framework", "spring mvc"], se_tag="spring-boot"),
    dict(id="dotnet", label=".NET", category="backend", aliases=[".net", "dotnet", "asp.net"], se_tag=".net"),
    dict(id="laravel", label="Laravel", category="backend", aliases=["laravel"], se_tag="laravel"),
    dict(id="fastapi", label="FastAPI", category="backend", aliases=["fastapi"], se_tag="fastapi"),
    # ---- data
    dict(id="postgresql", label="PostgreSQL", category="data", aliases=["postgres", "postgresql", "postgis"], se_tag="postgresql"),
    dict(id="mysql", label="MySQL", category="data", aliases=["mysql", "mariadb"], se_tag="mysql"),
    dict(id="mongodb", label="MongoDB", category="data", aliases=["mongodb", "mongo"], se_tag="mongodb"),
    dict(id="redis", label="Redis", category="data", aliases=["redis"], se_tag="redis"),
    dict(id="elasticsearch", label="Elasticsearch", category="data", aliases=["elasticsearch", "elastic search", "opensearch"], se_tag="elasticsearch"),
    dict(id="kafka", label="Kafka", category="data", aliases=["kafka"], se_tag="apache-kafka"),
    dict(id="spark", label="Spark", category="data", aliases=["apache spark", "pyspark", "spark sql"], se_tag="apache-spark"),
    dict(id="hadoop", label="Hadoop", category="data", aliases=["hadoop", "mapreduce"], se_tag="hadoop"),
    dict(id="airflow", label="Airflow", category="data", aliases=["airflow"], se_tag="airflow"),
    dict(id="snowflake", label="Snowflake", category="data", aliases=["snowflake"], se_tag="snowflake-cloud-data-platform"),
    dict(id="dbt", label="dbt", category="data", aliases=["dbt"], se_tag="dbt"),
    dict(id="pandas", label="pandas", category="data", aliases=["pandas"], se_tag="pandas"),
    # ---- AI / ML
    dict(id="ml", label="Machine Learning", category="ai", aliases=["machine learning", r"re:(?<![\w.])ml(?!\w)(?!\.\w)"], se_tag="machine-learning"),
    dict(id="deeplearning", label="Deep Learning", category="ai", aliases=["deep learning"], se_tag="deep-learning"),
    dict(id="tensorflow", label="TensorFlow", category="ai", aliases=["tensorflow"], se_tag="tensorflow"),
    dict(id="pytorch", label="PyTorch", category="ai", aliases=["pytorch"], se_tag="pytorch"),
    dict(id="sklearn", label="scikit-learn", category="ai", aliases=["scikit-learn", "sklearn"], se_tag="scikit-learn"),
    dict(id="cv", label="Computer Vision", category="ai", aliases=["computer vision"], se_tag="computer-vision"),
    dict(id="llm", label="LLM", category="ai", aliases=["llm", "llms", "large language model", "large language models"]),
    dict(id="genai", label="Generative AI", category="ai", aliases=["generative ai", "genai", "gen ai"]),
    dict(id="langchain", label="LangChain", category="ai", aliases=["langchain", "langgraph"], npm="langchain", se_tag="langchain"),
    dict(id="rag", label="RAG", category="ai", aliases=["retrieval augmented", "retrieval-augmented", r"cs:(?<![\w.])RAG(?!\w)(?!\.\w)"]),
    # ---- cloud / devops
    dict(id="aws", label="AWS", category="cloud", aliases=["aws", "amazon web services"], se_tag="amazon-web-services"),
    dict(id="gcp", label="GCP", category="cloud", aliases=["gcp", "google cloud"], se_tag="google-cloud-platform"),
    dict(id="azure", label="Azure", category="cloud", aliases=["azure"], se_tag="azure"),
    dict(id="docker", label="Docker", category="cloud", aliases=["docker"], se_tag="docker"),
    dict(id="kubernetes", label="Kubernetes", category="cloud", aliases=["kubernetes", "k8s"], se_tag="kubernetes"),
    dict(id="terraform", label="Terraform", category="cloud", aliases=["terraform"], se_tag="terraform"),
    dict(id="ansible", label="Ansible", category="cloud", aliases=["ansible"], se_tag="ansible"),
    dict(id="jenkins", label="Jenkins", category="cloud", aliases=["jenkins"], se_tag="jenkins"),
    dict(id="heroku", label="Heroku", category="cloud", aliases=["heroku"], se_tag="heroku"),
    dict(id="serverless", label="Serverless", category="cloud", aliases=["serverless"], se_tag="serverless"),
    dict(id="linux", label="Linux", category="cloud", aliases=["linux"], se_tag="linux"),
    # ---- mobile
    dict(id="android", label="Android", category="mobile", aliases=["android"], se_tag="android"),
    dict(id="ios", label="iOS", category="mobile", aliases=[r"cs:(?<![\w.])iOS(?!\w)(?!\.\w)"], se_tag="ios"),
    dict(id="reactnative", label="React Native", category="mobile", aliases=["react native", "react-native"], se_tag="react-native", npm="react-native"),
    dict(id="flutter", label="Flutter", category="mobile", aliases=["flutter"], se_tag="flutter"),
    # ---- other
    dict(id="blockchain", label="Blockchain", category="other", aliases=["blockchain", "smart contract", "solidity", "web3"], se_tag="solidity"),
]

BY_ID = {s["id"]: s for s in SKILLS}
assert len(BY_ID) == len(SKILLS), "duplicate skill id"


def _compile(alias):
    if alias.startswith("re:"):
        return re.compile(alias[3:], re.IGNORECASE)
    if alias.startswith("cs:"):
        return re.compile(alias[3:])
    return re.compile(W + re.escape(alias) + E, re.IGNORECASE)


@lru_cache(maxsize=1)
def patterns():
    return {s["id"]: [_compile(a) for a in s["aliases"]] for s in SKILLS}


_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def clean_html(text):
    """HN comments are HTML with entities; return plain text."""
    if not text:
        return ""
    text = html.unescape(_TAG.sub(" ", text))  # strip tags first, then decode entities such as &#x2F;
    return _WS.sub(" ", text).strip()


def extract_skills(text):
    """Return the sorted skill ids mentioned in already-cleaned text."""
    return sorted(sid for sid, pats in patterns().items() if any(p.search(text) for p in pats))
