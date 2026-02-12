############################################################
# Paper visualisations: Figures 2 and 3

# This script generates Figures 2 and 3 used in paper:
# "Working longer, feeling worse? How job quality shapes the mental health toll of delayed retirement"
# by Alexandra Lugova, Michele Belloni, Berangere Legendre, Jeremy Tanguy

# Currently implemented:
# 1) Figure 2: Estimated difference-in-difference effects of a one-year increase in the work horizon (ΔWHXPOST)
# on depression indicators (top panel: Euro-D score; bottom panel: Euro-D > 3) as a function on working conditions.

#2) Figure 1: Estimated difference-in-difference effects of an increase in the work horizon of more than one year ([ΔWH>1]XPOST)
# on depression indicators (top panel: Euro-D score; bottom panel: Euro-D > 3) as a function on working conditions.

############################################################

library(ggplot2)
library(dplyr)
library(tidyr)

# ---- Global settings ----
model_levels <- c("PEI", "SEI", "SDI", "WTQI", "II", "PI")
my_colors <- c("High quality" = "lightgreen", "Low quality" = "salmon")

# ---- Helper: build panel data from values + SEs ----
make_panel_df <- function(values, ses, stars, model_levels) {
  # values/ses/stars must be length 12 in this order:
  # PEI(H,L), SEI(H,L), SDI(H,L), WTQI(H,L), II(H,L), PI(H,L)
  stopifnot(length(values) == 12, length(ses) == 12, length(stars) == 12)
  
  df <- data.frame(
    model = rep(model_levels, each = 2),
    var   = rep(c("High quality", "Low quality"), times = length(model_levels)),
    value = values,
    se    = ses,
    stars = stars
  ) %>%
    mutate(
      ci_upper = value + 1.96 * se,
      ci_lower = value - 1.96 * se,
      model = factor(model, levels = model_levels)
    )
  
  df
}

# ---- Helper: plot one panel ----
plot_panel <- function(df, star_pad, ylab = "Estimated effect") {
  ggplot(df, aes(x = model, y = value, fill = var)) +
    geom_bar(stat = "identity", position = position_dodge(0.5), width = 0.6) +
    geom_errorbar(aes(ymin = ci_lower, ymax = ci_upper),
                  width = 0.2, position = position_dodge(0.5), color = "darkgrey") +
    geom_point(position = position_dodge(0.5), shape = 16, size = 1.5, color = "darkgrey") +
    geom_hline(yintercept = 0, linetype = "dashed", color = "darkgrey") +
    geom_text(aes(label = stars, y = ci_upper + star_pad),
              position = position_dodge(0.5),
              size = 5, color = "darkgrey") +
    labs(x = "Job Quality Index", y = ylab) +
    theme_light() +
    scale_fill_manual(values = my_colors) +
    scale_y_continuous(n.breaks = 7) +
    theme(
      axis.text.x  = element_text(size = 14),
      axis.text.y  = element_text(size = 14),
      axis.title.x = element_text(size = 16),
      axis.title.y = element_text(size = 16),
      legend.text  = element_text(size = 14),
      legend.title = element_blank()
    )
}

# ---- Panel inputs (values, SEs, stars) ----
# Order for each vector: PEI(H,L), SEI(H,L), SDI(H,L), WTQI(H,L), II(H,L), PI(H,L)

panels <- list(
  
  # Figure 2 — Euro-D, treatment ΔWH (continuous)
  eurod_wh = list(
    values = c(0.0289, 0.0663, -0.2906, 0.1394, -0.0728, 0.1336,
               0.0511, 0.0060,  0.0785, 0.0144, -0.0701, 0.1358),
    ses    = c(0.0593, 0.0582,  0.1301, 0.0313,  0.0507, 0.0474,
               0.0239, 0.0791,  0.0560, 0.0734,  0.0529, 0.0644),
    stars  = c("","","**","***","","***","**","","","","","**"),
    star_pad = 0.015
  ),
  
  # Figure 2 — Euro-D, treatment ΔWH>1 (categorical >1)
  eurod_whgt1 = list(
    values = c(0.0616, 0.2938, -1.4850, 0.5456, -0.3354, 0.5420,
               0.0974, 0.0545,  0.2935, 0.0622, -0.4462, 0.6264),
    ses    = c(0.2902, 0.2771,  0.6521, 0.2015,  0.2514, 0.2522,
               0.1964, 0.3348,  0.2813, 0.3433,  0.2398, 0.3197),
    stars  = c("","","**","***","","**","","","","","*","*"),
    star_pad = 0.07
  ),
  
  # Figure 3 — Euro-D > 3, treatment ΔWH (continuous)
  eurodcat_wh = list(
    values = c(0.0144, 0.0135, -0.0760, 0.0392, -0.0123, 0.0350,
               0.0141, 0.0086,  0.0145, 0.0122, -0.0095, 0.0340),
    ses    = c(0.0105, 0.0161,  0.0367, 0.0068,  0.0151, 0.0120,
               0.0092, 0.0238,  0.0138, 0.0188,  0.0151, 0.0143),
    stars  = c("","","**","***","","***","","","","","","**"),
    star_pad = 0.004
  ),
  
  # Figure 3 — Euro-D > 3, treatment ΔWH>1 (categorical >1)
  eurodcat_whgt1 = list(
    values = c(0.0652, 0.0588, -0.3531, 0.1678, -0.0409, 0.1566,
               0.0542, 0.0490,  0.0550, 0.0742, -0.0468, 0.1506),
    ses    = c(0.0495, 0.0743,  0.2095, 0.0400,  0.0669, 0.0576,
               0.0493, 0.0995,  0.0637, 0.0830,  0.0625, 0.0687),
    stars  = c("","","*","***","","***","","","","","","**"),
    star_pad = 0.02
  )
)

# ---- Build + plot all panels ----
plots <- lapply(names(panels), function(name) {
  info <- panels[[name]]
  df <- make_panel_df(info$values, info$ses, info$stars, model_levels)
  p  <- plot_panel(df, star_pad = info$star_pad)
  list(name = name, df = df, plot = p)
})
names(plots) <- names(panels)

# Print plots
print(plots$eurod_wh$plot)
print(plots$eurod_whgt1$plot)
print(plots$eurodcat_wh$plot)
print(plots$eurodcat_whgt1$plot)

# Optional saving:
# ggsave("figure2_eurod_wh.png", plots$eurod_wh$plot, width=8, height=5, dpi=600)
# ggsave("figure2_eurod_whgt1.png", plots$eurod_whgt1$plot, width=8, height=5, dpi=600)
# ggsave("figure3_eurodcat_wh.png", plots$eurodcat_wh$plot, width=8, height=5, dpi=600)
# ggsave("figure3_eurodcat_whgt1.png", plots$eurodcat_whgt1$plot, width=8, height=5, dpi=600)
