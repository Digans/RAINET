
## 20-Apr-2016 Diogo Ribeiro
## Script to create a ROC curve and provide statistics on comparing catRAPID predictions against experimentally determined interactions
## Used generally for all types of experimental datasets, NPInter, StarBase, eCLIP etc.

library(ggplot2)
library(reshape)
require(grid)
require(gridExtra)
library(data.table)
library(Epi)
library(ROCR)

#inputFile = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/StarBasePredictionValidation/lncRNAs/scores.tsv"
# inputFile = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/eCLIPPredictionValidation/ROC/eCLIP_background_plus_functional_lncRNAs/RPISeq/scores_RF.tsv"

###################################### 
# Input parsing 
###################################### 

shortVersion = 0

args <- commandArgs(TRUE)
# Test if we have enough arguments
if( length(args) != 3){
  stop("Rscript: Bad argument number")
}
inputFile = args[1]
outFolder = args[2]
shortVersion = args[3]

setwd(outFolder)

###################################### 
# Read input data
###################################### 

dataset <- fread(inputFile, stringsAsFactors = FALSE, header = TRUE, sep="\t")

# transform values
#dataset$catrapid_score = log10(dataset$catrapid_score)

# Separate validated from non-validated
validated = dataset[dataset$in_validated_set == 1,]
nonValidated = dataset[dataset$in_validated_set == 0]


###################################### 
###################################### 
#### Whole dataset 
###################################### 
###################################### 

### Basic statistics
paste("Number of experimental interactions:", nrow(validated))
paste("Number of non-experimental interactions:",nrow(nonValidated))
paste("Median score of experimental interactions:",median(validated$catrapid_score))
paste("Median score of non-experimental interactions:",median(nonValidated$catrapid_score))
paste("Kolmogorov-Smirnov pvalue:", ks.test(validated$catrapid_score, nonValidated$catrapid_score, alternative = c("two.sided"))$p.value)

###################################### 
# ROC curve 
###################################### 

# Use ROCR
pred = prediction(dataset$catrapid_score, dataset$in_validated_set, label.ordering = NULL)
perf = performance(pred, measure = "tpr", x.measure = "fpr")

auc = performance(pred, measure = "auc")

paste("AUC:", round(auc@y.values[[1]],2))

### Stop script if running only short version
if (shortVersion == 1){
  stop("short version of script ends here")
}


# ROC curve with ROCR package (fast)
plot(perf, ylab = "Sensitivity", xlab = "1-Specificity", lwd= 3, main = "ROC curve")
abline(a = 0, b = 1, col = "gray60")
text(0.9, 0.4, paste("AUC:",round(auc@y.values[[1]],2) ) )

# Optimal cutoff / cutpoint, best sensitivity and best specificity
cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
text(0.8,0.45, paste("Max(sens+spec):",round(cutoff,2) ) )

text(0.16,0.90, paste("# True:",nrow(validated) ) )
text(0.2,0.85, paste("# False:",nrow(nonValidated) ) )

colours = rainbow(3)

# Cutoff cost analysis. Augmenting weight of sensitivity
print ("cost cutoff sens 1-spec")
for (cost in seq(1,3)){
  calc = which.max(1-perf@x.values[[1]] + cost*perf@y.values[[1]])
  cutoff = perf@alpha.values[[1]][calc]
  sens = perf@y.values[[1]][calc]
  spec = 1-perf@x.values[[1]][calc]
#   print (paste(cost, cutoff , sens, spec) )
  points(x = 1-spec, y = sens, col = colours[cost], pch = 16)
}
legend("bottomright", paste("cost =", 1:3), col = colours[1:3], pch = 16, cex = 0.8, title = "Sensitivity")


###################################### 
# Plot catRAPID scores distributions in and outside StarBase
###################################### 
# 
# # testing difference of distributions (Kolmogorow-Smirnov  )
# ksTestWhole = ks.test(validated$catrapid_score, nonValidated$catrapid_score, alternative = c("two.sided"))
# 
# plt0 <- ggplot(dataset, aes(x=catrapid_score, colour = as.factor(in_validated_set))) + 
#   geom_density() + 
#   theme_minimal() +
#   xlab( "Score") +
#   ylab( "Density") +
#   annotate("text",  x=Inf, y = Inf, label = paste("# True: ",nrow(validated),"\n# False: ",nrow(dataset)-nrow(validated)), vjust=1, hjust=1) +
#   annotate("text",  x=Inf, y = 0, label = paste("KS test p-val: ", round(ksTestWhole$p.value,2)), vjust=1, hjust=1)
# plt0

# ###################################### 
# # Plot catRAPID scores versus CLIP reads mapped in StarBase
# ###################################### 
# 
# correlation = cor(validated$clipReads,validated$catrapid_score, method = "spearman")
# correlationSign = as.numeric(cor.test(validated$catrapid_score, validated$clipReads, method = "spearman")$p.value)
# correlationText = paste("Corr:", round(correlation,2),"(pval:", round(correlationSign),")")
# 
# plt1 <- ggplot(validated, aes(x = clipReads, y = catrapid_score)) + 
#   geom_point(shape=1) + 
#   geom_smooth(method=lm) + 
#   annotate("text", x = Inf, y = Inf, label = correlationText, hjust = 1, vjust =1  )
# plt1


###################################### 
###################################### 
#### Random subsamples : negatives
###################################### 
###################################### 
# Approach: Sub-sampling the non-validated dataset to match length of validated dataset, and keeping the validated dataset as it is

# parameters
repetitions = 100
nsubsample = nrow(validated)

colours = sample(colours(), repetitions)

cutoffs = c()
aurocs = c()
kss = c()

# Create ROC plots and other metrics
for (i in seq(1, repetitions)){
  # create subsample of non-validated set
  nonValidatedSample = nonValidated[sample( nrow(nonValidated), nsubsample ), ]
  datasetSample = rbind(nonValidatedSample, validated) 
  
  # ROC using ROCR on subsample
  pred = prediction(datasetSample$catrapid_score, datasetSample$in_validated_set, label.ordering = NULL)
  perf = performance(pred, measure = "tpr", x.measure = "fpr")
  if (i == 1){
    plot(perf, lty=5, col= colours[i], ylab = "Sensitivity", xlab = "1-Specificity", lwd= 3, main = "ROC curve: negatives subsampling")
  }else{
    plot(perf, lty=5, col= colours[i],main="", add=TRUE)
  }
  
  # Optimal cutoff / cutpoint
  cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
  cutoffs = c(cutoffs, cutoff)
  
  # AUROC
  auc = performance(pred, measure = "auc")
  aurocs = c(aurocs, auc@y.values[[1]])
}

# Mean cutoff and std of randomisations
cutoffText = paste("Mean cutoff:",round(mean(cutoffs),2),"std:",round(sd(cutoffs),2))
# Mean auc and std of randomisations
aucText = paste("Mean AUC:",round(mean(aurocs),2),"std:",round(sd(aurocs),2))

## adding more info to the plot
abline(a = 0, b = 1, col = "gray60")
text(0.7,0.3, paste("Subsample size:", nsubsample) )
text(0.7,0.2, paste("Number randomisations:", repetitions) )
text(0.7,0.1, cutoffText )
text(0.7,0.0, aucText )



###################################### 
###################################### 
#### Random subsamples : positives + negatives
###################################### 
###################################### 
# Approach: Sub-sampling the non-validated dataset to match length of validated dataset, and keeping the validated dataset as it is

# parameters
repetitions = 1000
nsubsample = nrow(validated) / 10 # change here 

colours = sample(colours(), repetitions)

cutoffs = c()
aurocs = c()
kss = c()

# Create ROC plots and other metrics
for (i in seq(1, repetitions)){
  # create subsample of non-validated set
  validatedSample = validated[sample( nrow(validated), nsubsample ), ]
  nonValidatedSample = nonValidated[sample( nrow(nonValidated), nsubsample), ]
  datasetSample = rbind(validatedSample, nonValidatedSample) 
  
  # ROC using ROCR on subsample
  pred = prediction(datasetSample$catrapid_score, datasetSample$in_validated_set, label.ordering = NULL)
  perf = performance(pred, measure = "tpr", x.measure = "fpr")
  if (i == 1){
    plot(perf, lty=5, col= colours[i], ylab = "Sensitivity", xlab = "1-Specificity", lwd= 3, main = "ROC curve: positive and negative subsampling")
  }else{
    plot(perf, lty=5, col= colours[i],main="", add=TRUE)
  }
  
  # Optimal cutoff / cutpoint
  cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
  cutoffs = c(cutoffs, cutoff)
  
  # AUROC
  auc = performance(pred, measure = "auc")
  aurocs = c(aurocs, auc@y.values[[1]])
}

# Mean cutoff and std of randomisations
cutoffText = paste("Mean cutoff:",round(mean(cutoffs),2),"std:",round(sd(cutoffs),2))
# Mean auc and std of randomisations
aucText = paste("Mean AUC:",round(mean(aurocs),2),"std:",round(sd(aurocs),2))

## adding more info to the plot
abline(a = 0, b = 1, col = "gray60")
text(0.7,0.3, paste("Subsample size:", nsubsample) )
text(0.7,0.2, paste("Number randomisations:", repetitions) )
text(0.7,0.1, cutoffText )
text(0.7,0.0, aucText )



###################################### 
# Adding noise to dataset (missing information / stability analysis) 
###################################### 
# How does the ROC behave if I introduce some previously negatives as being positives

# parameters
repetitions = 5
sampleSize = nrow(validated) #/10 # how many negatives becoming positives

cutoffs = c()
aurocs = c()

for (i in seq(1, repetitions)){
  
  print(paste("Repetition:",i) )
  
  # randomly pick indexes from negatives of where to make change
  indexesToChange = sample( nrow(nonValidated), sampleSize )
  
  # create new copy of nonValidated, which will be modified
  copyNonValidated = nonValidated
  
  # now the non validated set will contain some validated items
  copyNonValidated$in_validated_set[indexesToChange] = 1
  
  # join 'non'-validated and validated
  datasetSample = rbind(validated,copyNonValidated) 
  
  # ROC using ROCR
  pred = prediction(datasetSample$catrapid_score, datasetSample$in_validated_set, label.ordering = NULL)
  perf = performance(pred, measure = "tpr", x.measure = "fpr")
  if (i == 1){
    plot(perf, lty=5, col= colours[i], ylab = "Sensitivity", xlab = "1-Specificity", main = "ROC curve, noise addition")
  }else{
    plot(perf, lty=5, col= colours[i],main="", add=TRUE)
  }
  
  # Optimal cutoff / cutpoint
  cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
  cutoffs = c(cutoffs, cutoff)
  
  # AUROC
  auc = performance(pred, measure = "auc")
  aurocs = c(aurocs, auc@y.values[[1]])
  
}
# Add the original (before noise introduced) ROC line
pred = prediction(dataset$catrapid_score, dataset$in_validated_set, label.ordering = NULL)
perf = performance(pred, measure = "tpr", x.measure = "fpr")
plot(perf, lwd = 3, lty=1, col= "black",main="", add=TRUE)

# Mean cutoff and std of randomisations
cutoffText = paste("Mean cutoff:",round(mean(cutoffs),2),"std:",round(sd(cutoffs),2))
# Mean auc and std of randomisations
aucText = paste("Mean AUC:",round(mean(aurocs),2),"std:",round(sd(aurocs),2))

## adding more info to the plot
abline(a = 0, b = 1, col = "gray60")
text(0.7,0.3, paste("# Noise items:", sampleSize) )
text(0.7,0.2, paste("Number randomisations:", repetitions) )
text(0.7,0.1, cutoffText )
text(0.7,0.0, aucText )


# ###################################### 
# ###################################### 
# # StarBase + NPInter
# ###################################### 
# ###################################### 
# 
# inputFile1 = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/NPInterPredictionValidation/allInteractions/scores.tsv"
# inputFile2 = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/StarBasePredictionValidation/lncRNAs/scores.tsv"
# 
# dataset1 <- fread(inputFile1, stringsAsFactors = FALSE, header = TRUE, sep="\t")
# dataset2 <- fread(inputFile2, stringsAsFactors = FALSE, header = TRUE, sep="\t")
# 
# nrow(dataset1[dataset1$in_validated_set == 1])
# nrow(dataset2[dataset2$in_validated_set == 1])
# 
# # new dataset
# dataset <- dataset2
# 
# ## merge the in validated from both files
# if (nrow(dataset1) == nrow(dataset2)){
#   
#   #check which indexes of dataset1 are true
#   indexesToChange = which(dataset1$in_validated_set == 1)
#   
#   # change de items on dataset 2 to be true if they are in dataset1
#   dataset$in_validated_set[indexesToChange] = 1
# }
# 
# nrow(dataset[dataset$in_validated_set == 1])
# 
# # Use ROCR
# pred = prediction(dataset$catrapid_score, dataset$in_validated_set, label.ordering = NULL)
# 
# perf = performance(pred, measure = "tpr", x.measure = "fpr")
# 
# # ROC curve with ROCR package (fast)
# plot(perf, ylab = "Sensitivity", xlab = "1-Specificity", lwd= 3, main = "ROC curve of whole dataset")
# abline(a = 0, b = 1, col = "gray60")
# 
# auc = performance(pred, measure = "auc")
# text(0.9, 0.4, paste("AUC:",round(auc@y.values[[1]],2) ) )
# 
# # Optimal cutoff / cutpoint, best sensitivity and best specificity
# cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
# cutoff
# text(0.7,0.45, paste("Cutoff[Max(sens+spec)]:",round(cutoff,2) ) )
# 
# colours = rainbow(5)
# 
# # Cutoff cost analysis. Augmenting weight of sensitivity
# print ("cost cutoff sens 1-spec")
# for (cost in seq(1,5)){
#   calc = which.max(1-perf@x.values[[1]] + cost*perf@y.values[[1]])
#   cutoff = perf@alpha.values[[1]][calc]
#   sens = perf@y.values[[1]][calc]
#   spec = 1-perf@x.values[[1]][calc]
#   print (paste(cost, cutoff , sens, spec) )
#   points(x = 1-spec, y = sens, col = colours[cost], pch = 16)
# }
# legend("bottomright", paste("cost =", 1:5), col = colours[1:5], pch = 16, cex = 0.8, title = "Sensitivity")



# ###################################### 
# ###################################### 
# # StarBase + NPInter FOR JOBIM 26-June-2016
# ###################################### 
# ###################################### 
# 
# inputFile1 = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/NPInterPredictionValidation/allInteractions/scores.tsv"
# inputFile2 = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/StarBasePredictionValidation/lncRNAs/scores.tsv"
# 
# dataset1 <- fread(inputFile1, stringsAsFactors = FALSE, header = TRUE, sep="\t")
# dataset2 <- fread(inputFile2, stringsAsFactors = FALSE, header = TRUE, sep="\t")
# 
# nrow(dataset1[dataset1$in_validated_set == 1])
# nrow(dataset2[dataset2$in_validated_set == 1])
# 
# # new dataset
# dataset <- dataset2
# 
# ## merge the in validated from both files
# if (nrow(dataset1) == nrow(dataset2)){
#   
#   #check which indexes of dataset1 are true
#   indexesToChange = which(dataset1$in_validated_set == 1)
#   
#   # change de items on dataset 2 to be true if they are in dataset1
#   dataset$in_validated_set[indexesToChange] = 1
# }
# 
# positives = nrow(dataset[dataset$in_validated_set == 1])
# negatives = nrow(dataset[dataset$in_validated_set == 0])
# 
# # Use ROCR
# pred = prediction(dataset$catrapid_score, dataset$in_validated_set, label.ordering = NULL)
# 
# perf = performance(pred, measure = "tpr", x.measure = "fpr")
# 
# # ROC curve with ROCR package (fast)
# plot(perf, ylab = "True positive rate", xlab = "False positive rate", lwd= 3, main = "ROC curve: NPInter + StarBase datasets")
# abline(a = 0, b = 1, col = "gray60")
# 
# auc = performance(pred, measure = "auc")
# text(0.9, 0.4, paste("AUC:",round(auc@y.values[[1]],2) ) )
# 
# # Optimal cutoff / cutpoint, best sensitivity and best specificity
# cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
# cutoff
# text(0.8,0.45, paste("Max(sens+spec):",round(cutoff,2) ) )
# 
# text(0.16,0.90, paste("Positives:",positives ) )
# text(0.2,0.85, paste("Negatives:",negatives ) )
# 
# colours = rainbow(3)
# 
# # Cutoff cost analysis. Augmenting weight of sensitivity
# print ("cost cutoff sens 1-spec")
# for (cost in seq(1,3)){
#   calc = which.max(1-perf@x.values[[1]] + cost*perf@y.values[[1]])
#   cutoff = perf@alpha.values[[1]][calc]
#   sens = perf@y.values[[1]][calc]
#   spec = 1-perf@x.values[[1]][calc]
#   print (paste(cost, cutoff , sens, spec) )
#   points(x = 1-spec, y = sens, col = colours[cost], pch = 16)
# }
# legend("bottomright", paste("cost =", 1:3), col = colours[1:3], pch = 16, cex = 0.8, title = "Sensitivity")
# 


# ###################################### 
# ###################################### 
# # StarBase FOR ANDREAS FOR JOBIM 26-June-2016
# ###################################### 
# ###################################### 
# 
# inputFile = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/StarBasePredictionValidation/mRNAs/scores.tsv"
# inputFile = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/StarBasePredictionValidation/mRNAs/stringent/scores.tsv"
# inputFile = "/home/diogo/Documents/RAINET_data/TAGC/rainetDatabase/results/StarBasePredictionValidation/mRNAs/extraStringent/scores.tsv"
# 
# dataset <- fread(inputFile, stringsAsFactors = FALSE, header = TRUE, sep="\t")
# 
# # Use ROCR
# pred = prediction(dataset$catrapid_score, dataset$in_validated_set, label.ordering = NULL)
# 
# perf = performance(pred, measure = "tpr", x.measure = "fpr")
# 
# # ROC curve with ROCR package (fast)
# plot(perf, ylab = "True positive rate", xlab = "False positive rate", lwd= 3, main = "ROC curve: StarBase mRNA dataset")
# abline(a = 0, b = 1, col = "gray60")
# 
# auc = performance(pred, measure = "auc")
# text(0.9, 0.4, paste("AUC:",round(auc@y.values[[1]],2) ) )
# 
# # Optimal cutoff / cutpoint, best sensitivity and best specificity
# cutoff = perf@alpha.values[[1]][which.max(1-perf@x.values[[1]] + perf@y.values[[1]])] 
# cutoff
# text(0.8,0.45, paste("Max(sens+spec):",round(cutoff,2) ) )
# 
# colours = rainbow(3)
# 
# # Cutoff cost analysis. Augmenting weight of sensitivity
# print ("cost cutoff sens 1-spec")
# for (cost in seq(1,3)){
#   calc = which.max(1-perf@x.values[[1]] + cost*perf@y.values[[1]])
#   cutoff = perf@alpha.values[[1]][calc]
#   sens = perf@y.values[[1]][calc]
#   spec = 1-perf@x.values[[1]][calc]
#   print (paste(cost, cutoff , sens, spec) )
#   points(x = 1-spec, y = sens, col = colours[cost], pch = 16)
# }
# legend("bottomright", paste("cost =", 1:3), col = colours[1:3], pch = 16, cex = 0.8, title = "Sensitivity")
