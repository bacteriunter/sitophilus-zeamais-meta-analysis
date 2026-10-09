# ============================================================
# 39_mortality_main_figure.R
# Mortalidad final por estudio, tratamiento y dosis
# ============================================================

project <- path.expand("~/sitophilus_meta")

input <- file.path(
  project,
  "07_meta_analysis",
  "mortality_meta_dataset.csv"
)

figdir <- file.path(
  project,
  "08_figures"
)

dir.create(
  figdir,
  recursive = TRUE,
  showWarnings = FALSE
)

dat <- read.csv(
  input,
  stringsAsFactors = FALSE
)


# ============================================================
# VALIDACIONES
# ============================================================

stopifnot(nrow(dat) == 154)
stopifnot(length(unique(dat$study_id)) == 9)

dat <- dat[
  order(
    dat$study_id,
    dat$treatment,
    dat$dose_numeric
  ),
]


# ============================================================
# ETIQUETA ESTUDIO + TRATAMIENTO
# ============================================================

dat$study_treatment <- paste(
  dat$study_id,
  dat$treatment,
  sep = " | "
)


# Orden de tratamientos según estudio
levels_order <- unique(
  dat$study_treatment
)

dat$study_treatment <- factor(
  dat$study_treatment,
  levels = rev(levels_order)
)


# ============================================================
# INFORMACIÓN PARA SEPARAR ESTUDIOS
# ============================================================

treatment_info <- unique(
  dat[
    ,
    c(
      "study_id",
      "study_treatment"
    )
  ]
)

treatment_info$study_treatment <- factor(
  treatment_info$study_treatment,
  levels = levels(dat$study_treatment)
)

treatment_info <- treatment_info[
  order(treatment_info$study_treatment),
]


# ============================================================
# FUNCIÓN PARA GENERAR FIGURA
# ============================================================

make_plot <- function() {

  par(
    mar = c(5, 19, 3, 2)
  )

  y <- as.numeric(
    dat$study_treatment
  )

  plot(
    dat$mortality_pct,
    y,
    xlim = c(0, 105),
    ylim = c(
      0.5,
      length(levels(dat$study_treatment)) + 0.5
    ),
    xlab = "Final mortality (%)",
    ylab = "",
    yaxt = "n",
    pch = 16,
    cex = 0.9
  )

  # ----------------------------------------------------------
  # Líneas horizontales suaves
  # ----------------------------------------------------------

  abline(
    h = seq_along(
      levels(dat$study_treatment)
    ),
    lty = 3
  )


  # ----------------------------------------------------------
  # Volver a dibujar puntos sobre las líneas
  # ----------------------------------------------------------

    # ----------------------------------------------------------
  # Conectar dosis dentro de cada tratamiento
  #
  # Las líneas unen las observaciones de menor a mayor dosis.
  # No representan un modelo ni una regresión.
  # ----------------------------------------------------------

  treatment_levels <- unique(
    as.character(dat$study_treatment)
  )

  for (tr in treatment_levels) {

    idx <- which(
      as.character(dat$study_treatment) == tr
    )

    sub <- dat[idx, ]

    sub <- sub[
      order(sub$dose_numeric),
    ]

    yy <- as.numeric(
      sub$study_treatment
    )

    if (nrow(sub) > 1) {

      lines(
        sub$mortality_pct,
        yy,
        lwd = 1.2
      )
    }
  }


  # ----------------------------------------------------------
  # Dibujar puntos sobre las líneas
  # ----------------------------------------------------------

  points(
    dat$mortality_pct,
    y,
    pch = 16,
    cex = 0.9
  )


  # ----------------------------------------------------------
  # Etiquetas
  # ----------------------------------------------------------

  axis(
    2,
    at = seq_along(
      levels(dat$study_treatment)
    ),
    labels = levels(
      dat$study_treatment
    ),
    las = 1,
    cex.axis = 0.65
  )


  # ----------------------------------------------------------
  # Líneas verticales de referencia
  # ----------------------------------------------------------

  abline(
    v = c(25, 50, 75),
    lty = 2
  )


  # ----------------------------------------------------------
  # Marcar mortalidad corregida
  # ----------------------------------------------------------

  corrected <- (
    dat$mortality_basis == "CORRECTED"
  )

  if (any(corrected)) {

    points(
      dat$mortality_pct[corrected],
      y[corrected],
      pch = 1,
      cex = 1.5,
      lwd = 1.4
    )
  }


  # ----------------------------------------------------------
  # Leyenda
  # ----------------------------------------------------------

  legend(
    "bottomright",
    legend = c(
      "Reported mortality",
      "Corrected mortality"
    ),
    pch = c(16, 1),
    pt.cex = c(0.9, 1.4),
    bty = "n"
  )

  title(
    main =
      "Final mortality of Sitophilus zeamais across natural treatments"
  )
}


# ============================================================
# PNG
# ============================================================

png(
  filename = file.path(
    figdir,
    "mortality_by_study_treatment.png"
  ),
  width = 2600,
  height = 2400,
  res = 220
)

make_plot()

dev.off()


# ============================================================
# PDF
# ============================================================

pdf(
  file = file.path(
    figdir,
    "mortality_by_study_treatment.pdf"
  ),
  width = 12,
  height = 11
)

make_plot()

dev.off()


# ============================================================
# TABLA PARA AUDITAR LA FIGURA
# ============================================================

figure_data <- dat[
  ,
  c(
    "study_id",
    "experiment_id_meta",
    "treatment",
    "dose_numeric",
    "dose_unit",
    "mortality_pct",
    "mortality_basis"
  )
]

figure_csv <- file.path(
  figdir,
  "mortality_by_study_treatment_data.csv"
)

write.csv(
  figure_data,
  figure_csv,
  row.names = FALSE
)


# ============================================================
# RESUMEN
# ============================================================

cat("\n==========================================")
cat("\nFIGURA PRINCIPAL DE MORTALIDAD")
cat("\n==========================================\n")

cat("\nObservaciones:", nrow(dat))
cat("\nEstudios:", length(unique(dat$study_id)))
cat("\nTratamientos:", length(unique(dat$treatment_id)))

cat(
  "\nMortalidad RAW:",
  sum(dat$mortality_basis == "RAW")
)

cat(
  "\nMortalidad CORRECTED:",
  sum(dat$mortality_basis == "CORRECTED")
)

cat("\n\nRango por estudio:\n\n")

study_range <- aggregate(
  mortality_pct ~ study_id,
  data = dat,
  FUN = function(x) {
    paste0(
      round(min(x), 2),
      " - ",
      round(max(x), 2)
    )
  }
)

print(
  study_range,
  row.names = FALSE
)

cat("\n==========================================")
cat("\nARCHIVOS GENERADOS")
cat("\n==========================================\n")

cat(
  "\nPNG:\n",
  file.path(
    figdir,
    "mortality_by_study_treatment.png"
  ),
  "\n"
)

cat(
  "\nPDF:\n",
  file.path(
    figdir,
    "mortality_by_study_treatment.pdf"
  ),
  "\n"
)

cat(
  "\nDatos de figura:\n",
  figure_csv,
  "\n\n"
)
