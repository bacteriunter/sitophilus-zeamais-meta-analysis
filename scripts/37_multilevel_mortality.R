# ============================================================
# 37_multilevel_mortality.R
# Síntesis cuantitativa multinivel de mortalidad reportada
# ============================================================

library(lme4)

project <- path.expand("~/sitophilus_meta")

input <- file.path(
  project,
  "07_meta_analysis",
  "mortality_meta_dataset.csv"
)

outdir <- file.path(
  project,
  "07_meta_analysis"
)

dir.create(
  outdir,
  recursive = TRUE,
  showWarnings = FALSE
)

dat <- read.csv(
  input,
  stringsAsFactors = FALSE
)

# ------------------------------------------------------------
# Función inversa logit
# ------------------------------------------------------------

invlogit <- function(x) {
  exp(x) / (1 + exp(x))
}


# ------------------------------------------------------------
# Función para ajustar modelo
# ------------------------------------------------------------

fit_model <- function(d, label) {

  cat("\n")
  cat("====================================================\n")
  cat(label, "\n")
  cat("====================================================\n\n")

  cat("Observaciones:", nrow(d), "\n")
  cat(
    "Estudios:",
    length(unique(d$study_id)),
    "\n"
  )
  cat(
    "Experimentos:",
    length(unique(d$experiment_id_meta)),
    "\n"
  )
  cat(
    "Tratamientos:",
    length(unique(d$treatment_id)),
    "\n\n"
  )

  # ----------------------------------------------------------
  # Modelo:
  # observaciones anidadas en tratamiento,
  # tratamiento dentro de experimento,
  # experimento dentro de estudio.
  # ----------------------------------------------------------

  model <- lmer(
    mortality_logit ~ 1 +
      (1 | study_id) +
      (1 | experiment_id_meta) +
      (1 | treatment_id),
    data = d,
    REML = TRUE
  )

  print(summary(model))

  # ----------------------------------------------------------
  # Estimación global
  # ----------------------------------------------------------

  beta <- fixef(model)[1]

  mortality_prop <- invlogit(beta)
  mortality_pct <- mortality_prop * 100

  # IC aproximado del efecto fijo
  se_beta <- sqrt(
    vcov(model)[1, 1]
  )

  ci_low <- beta - 1.96 * se_beta
  ci_high <- beta + 1.96 * se_beta

  pct_low <- invlogit(ci_low) * 100
  pct_high <- invlogit(ci_high) * 100

  cat("\n--------------------------------------------\n")
  cat("ESTIMACIÓN GLOBAL\n")
  cat("--------------------------------------------\n")

  cat(
    "Logit:",
    round(beta, 4),
    "\n"
  )

  cat(
    "Mortalidad estimada (%):",
    round(mortality_pct, 2),
    "\n"
  )

  cat(
    "IC95%:",
    round(pct_low, 2),
    "-",
    round(pct_high, 2),
    "\n"
  )


  # ----------------------------------------------------------
  # Componentes de varianza
  # ----------------------------------------------------------

  vc <- as.data.frame(
    VarCorr(model)
  )

  cat("\n--------------------------------------------\n")
  cat("COMPONENTES DE VARIANZA\n")
  cat("--------------------------------------------\n")

  print(
    vc[
      ,
      c(
        "grp",
        "vcov",
        "sdcor"
      )
    ]
  )


  # ----------------------------------------------------------
  # Singularidad
  # ----------------------------------------------------------

  singular <- isSingular(
    model,
    tol = 1e-4
  )

  cat(
    "\nModelo singular:",
    singular,
    "\n"
  )


  # ----------------------------------------------------------
  # Devolver resultados
  # ----------------------------------------------------------

  result <- data.frame(
    analysis = label,
    observations = nrow(d),
    studies = length(
      unique(d$study_id)
    ),
    experiments = length(
      unique(d$experiment_id_meta)
    ),
    treatments = length(
      unique(d$treatment_id)
    ),
    logit = beta,
    SE = se_beta,
    mortality_pct = mortality_pct,
    CI95_low = pct_low,
    CI95_high = pct_high,
    singular = singular
  )

  return(
    list(
      model = model,
      result = result
    )
  )
}


# ============================================================
# 1. MODELO PRINCIPAL
# ============================================================

main <- fit_model(
  dat,
  "PRIMARY_ALL"
)


# ============================================================
# 2. SENSIBILIDAD:
# excluir mortalidad corregida
# ============================================================

raw_dat <- dat[
  dat$mortality_basis == "RAW",
]

sens_raw <- fit_model(
  raw_dat,
  "SENSITIVITY_RAW_ONLY"
)


# ============================================================
# 3. SENSIBILIDAD:
# excluir valores 0 y 100
# ============================================================
# Convertir explícitamente el indicador a lógico
boundary_logical <- tolower(
  as.character(dat$boundary_0_100)
) %in% c("true", "1", "yes")

non_boundary <- dat[
  !boundary_logical,
]

cat(
  "\nObservaciones después de excluir 0/100:",
  nrow(non_boundary),
  "\n"
)

sens_boundary <- fit_model(
  non_boundary,
  "SENSITIVITY_NO_0_100"
)


# ============================================================
# COMBINAR RESULTADOS
# ============================================================

results <- rbind(
  main$result,
  sens_raw$result,
  sens_boundary$result
)

outfile <- file.path(
  outdir,
  "multilevel_mortality_results.csv"
)

write.csv(
  results,
  outfile,
  row.names = FALSE
)


cat("\n")
cat("====================================================\n")
cat("RESUMEN FINAL\n")
cat("====================================================\n\n")

print(
  results,
  row.names = FALSE
)

cat(
  "\nResultados:\n",
  outfile,
  "\n"
)
