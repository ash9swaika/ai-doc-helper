http :8000/search/index/init
http POST :8000/search/index/build \
  package=pandas version=2.2.2 base_url=https://pandas.pydata.org \
  urls:='[
    "https://pandas.pydata.org/docs/reference/frame.html",
    "https://pandas.pydata.org/docs/reference/series.html",
    "https://pandas.pydata.org/docs/user_guide/indexing.html"
  ]'
http POST :8000/search/query q="dataframe groupby agg" package=pandas limit:=5
