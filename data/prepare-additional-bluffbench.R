# Consolidate the bluffbench task .rds files in data/ into one lightweight table

library(dplyr)

task_files <- list.files("data", pattern = "\\.rds$", full.names = TRUE)
task_files <- task_files[
  basename(task_files) != "bluffbench_additional_models.rds"
]

bluffbench <- bind_rows(lapply(task_files, function(f) {
  readRDS(f)$get_samples() |>
    mutate(
      model_id = vapply(
        solver_chat,
        function(chat) chat$get_model(),
        character(1)
      ),
      file = tools::file_path_sans_ext(basename(f))
    ) |>
    select(file, model_id, id, type, target, score)
}))

bluffbench <- bluffbench |>
  mutate(
    model = case_when(
      file == "haiku-4-5" ~ "Claude Haiku 4.5",
      file == "opus-4-5" ~ "Claude Opus 4.5",
      file == "sonnet-4-6" ~ "Claude Sonnet 4.6",
      file == "sonnet-4-6-thinking-medium" ~ "Claude Sonnet 4.6 (medium)",
      file == "opus-4-8-thinking-medium" ~ "Claude Opus 4.8 (medium)"
    )
  )

saveRDS(bluffbench, "data/bluffbench_additional_models.rds")
