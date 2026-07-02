library(tidyverse)

files <- c(
  "data/haiku-4-5.rds",
  "data/opus-4-8-thinking-medium.rds",
  "data/sonnet-4-6-thinking-medium.rds",
  "data/sonnet-4-6.rds"
)

# Per-million-token prices for models with NA cost
prices <- tribble(
  ~model                      , ~input_price , ~output_price , ~cached_input_price ,
  "Anthropic/claude-opus-4-8" ,            5 ,            25 , 6.25
)

extract_solver_info <- function(file) {
  task <- readRDS(file)
  samples <- task$get_samples()

  chat1 <- samples$solver_chat[[1]]
  model_name <- sub(
    ".*<Chat (.+?) turns=.*",
    "\\1",
    capture.output(print(chat1))[1]
  )

  map_dfr(seq_len(nrow(samples)), function(i) {
    tokens <- samples$solver_chat[[i]]$get_tokens()
    tibble(
      model = model_name,
      input_tokens = sum(tokens$input, na.rm = TRUE),
      output_tokens = sum(tokens$output, na.rm = TRUE),
      cached_input_tokens = sum(tokens$cached_input, na.rm = TRUE),
      cost = {
        c <- sum(as.numeric(tokens$cost), na.rm = TRUE)
        if (c == 0) NA_real_ else c
      }
    )
  })
}

solver_info <- map_dfr(files, extract_solver_info)

solver_costs <- solver_info |>
  left_join(prices, by = "model") |>
  mutate(
    cost = coalesce(
      cost,
      (input_tokens *
        input_price +
        output_tokens * output_price +
        cached_input_tokens * cached_input_price) /
        1e6
    )
  ) |>
  group_by(model) |>
  summarise(
    input = sum(input_tokens),
    output = sum(output_tokens),
    cached_input = sum(cached_input_tokens),
    cost = sum(cost)
  )

solver_costs
