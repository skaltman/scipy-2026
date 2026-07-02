# Same model at every rung — only the harness changes. That's the whole point:
# any difference the audience sees is the scaffolding, not a smarter model.

library(ellmer)
library(btw)

model <- "claude-sonnet-4-6" # swap to "claude-opus-4-8" to show even the best model can't see data it isn't given
prompt <- "Explore `df` and tell me about the data."

# A tiny made-up table — small enough to paste straight into the prompt, and
# unmemorized, so the raw model has nothing to fall back on but this data.
# Swap in the real dataset later.
df <- tibble::tribble(
  ~patient , ~arm      , ~dose_mg , ~response ,
  "P01"    , "placebo" ,        0 , 1.9       ,
  "P02"    , "placebo" ,        0 , 2.3       ,
  "P03"    , "low"     ,       25 , 4.1       ,
  "P04"    , "low"     ,       25 , 3.8       ,
  "P05"    , "high"    ,       50 , 6.5       ,
  "P06"    , "high"    ,       50 , 6.9
)

# ---- Rung 0: raw model, no harness ------------------------------------------
# Never seen `df`. It can only generalize or invent — a performance.
raw <- chat_anthropic(model = model)
raw$chat(prompt, df)


# ---- Rung 1: the actual data, but still no tools ----------------------------
# Paste the literal rows into the prompt. It can see the real data now, but
# still can't run anything, verify, or iterate.
described <- chat_anthropic(model = model)
described$chat(paste(capture.output(print(df)), collapse = "\n"), prompt)

# ---- Rung 2: give it tools — the harness ------------------------------------
# btw_client() registers btw_tools() (a run-R tool + data-frame inspectors), so
# the model executes R in this session and grounds every claim in real output.
# path_btw/path_llms_txt = FALSE keeps the demo reproducible (no local context).
harnessed <- btw_client(
  client = paste0("anthropic/", model),
  path_btw = FALSE,
  path_llms_txt = FALSE
)
harnessed$chat(prompt)
