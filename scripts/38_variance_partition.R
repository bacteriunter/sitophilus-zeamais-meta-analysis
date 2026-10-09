# ============================================================
# 38_variance_partition.R
# Partición de la variabilidad del modelo multinivel
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

figdir <- file.path(
  project,
  "08_figures"
)

dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
dir.create(figdir, recursive = TRUE, showWarnings = FALSE)


# ============================================================
# DATOS
# ============================================================

dat <- read.csv(
  input,
  stringsAsFactors = FALSE
)

cat("\n==========================================")
cat("\nPARTICIÓN DE VARIANZA")
cat("\n==========================================\n")

cat("\nObservaciones:", nrow(dat))
cat("\nEstudios:", length(unique(dat$study_id)))
cat("\nExperimentos:", length(unique(dat$experiment_id_meta)))
cat("\nTratamientos:", length(unique(dat$treatment_id)), "\n")


# ============================================================
# MODELO PRINCIPAL
# ============================================================

model <- lmer(
  mortality_logit ~ 1 +
    (1 | study_id) +
    (1 | experiment_id_meta) +
    (1 | treatment_id),
  data = dat,
  REML = TRUE
)


# ============================================================
# EXTRAER COMPONENTES DE VARIANZA
# ============================================================

vc <- as.data.frame(
  VarCorr(model)
)

variance_table <- data.frame(
  level = c(
    "Study",
    "Experiment",
    "Treatment",
    "Residual"
  ),
  variance = c(
    vc$vcov[vc$grp == "study_id"],
    vc$vcov[vc$grp == "experiment_id_meta"],
    vc$vcov[vc$grp == "treatment_id"],
    vc$vcov[vc$grp == "Residual"]
  )
)

variance_table$total_variance <- sum(
  variance_table$variance
)

variance_table$proportion <- (
  variance_table$variance /
  variance_table$total_variance
)

variance_table$percentage <- (
  variance_table$proportion * 100
)


# ============================================================
# ORDENAR
# ============================================================

variance_table$level <- factor(
  variance_table$level,
  levels = c(
    "Study",
    "Experiment",
    "Treatment",
    "Residual"
  )
)


# ============================================================
# GUARDAR TABLA
# ============================================================

output_csv <- file.path(
  outdir,
  "mortality_variance_partition.csv"
)

write.csv(
  variance_table,
  output_csv,
  row.names = FALSE
)


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

cat("\n==========================================")
cat("\nCOMPONENTES DE VARIANZA")
cat("\n==========================================\n\n")

print(
  variance_table[
    ,
    c(
      "level",
      "variance",
      "percentage"
    )
  ],
  row.names = FALSE
)

cat(
  "\nVarianza total:",
  round(
    unique(
      variance_table$total_variance
    ),
    4
  ),
  "\n"
)


# ============================================================
# ICC DEL ESTUDIO
#
# Proporción de la varianza total atribuible
# a diferencias entre estudios.
# ============================================================

study_variance <- variance_table$variance[
  variance_table$level == "Study"
]

total_variance <- unique(
  variance_table$total_variance
)

ICC_study <- (
  study_variance /
  total_variance
)

cat(
  "\nICC estudio:",
  round(ICC_study, 4)
)

cat(
  "\nPorcentaje atribuible al estudio:",
  round(ICC_study * 100, 2),
  "%\n"
)


# ============================================================
# FIGURA
# ============================================================

png(
  filename = file.path(
    figdir,
    "mortality_variance_partition.png"
  ),
  width = 1800,
  height = 1300,
  res = 200
)

par(
  mar = c(5, 8, 3, 2)
)

bp <- barplot(
  rev(variance_table$percentage),
  names.arg = rev(
    as.character(
      variance_table$level
    )
  ),
  horiz = TRUE,
  xlab = "Percentage of total variance",
  las = 1,
  xlim = c(
    0,
    max(variance_table$percentage) * 1.20
  ),
  border = NA
)

text(
  x = rev(variance_table$percentage) + 1,
  y = bp,
  labels = paste0(
    round(
      rev(variance_table$percentage),
      1
    ),
    "%"
  ),
  pos = 4
)

title(
  main = "Variance partition of reported mortality"
)

dev.off()


# ============================================================
# PDF
# ============================================================

pdf(
  file = file.path(
    figdir,
    "mortality_variance_partition.pdf"
  ),
  width = 8,
  height = 5.5
)

par(
  mar = c(5, 8, 3, 2)
)

bp <- barplot(
  rev(variance_table$percentage),
  names.arg = rev(
    as.character(
      variance_table$level
    )
  ),
  horiz = TRUE,
  xlab = "Percentage of total variance",
  las = 1,
  xlim = c(
    0,
    max(variance_table$percentage) * 1.20
  ),
  border = NA
)

text(
  x = rev(variance_table$percentage) + 1,
  y = bp,
  labels = paste0(
    round(
      rev(variance_table$percentage),
      1
    ),
    "%"
  ),
  pos = 4
)

title(
  main = "Variance partition of reported mortality"
)

dev.off()


# ============================================================
# FINAL
# ============================================================

cat("\n==========================================")
cat("\nARCHIVOS GENERADOS")
cat("\n==========================================\n")

cat(
  "\nTabla:\n",
  output_csv,
  "\n"
)

cat(
  "\nFigura PNG:\n",
  file.path(
    figdir,
    "mortality_variance_partition.png"
  ),
  "\n"
)

cat(
  "\nFigura PDF:\n",
  file.path(
    figdir,
    "mortality_variance_partition.pdf"
  ),
  "\n"
)

cat("\n")
