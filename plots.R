library(zoo)

args = commandArgs(trailingOnly = TRUE)
print("Trying to open:")
print(paste(args[1], ".record", sep=""))
print(paste(args[1], ".database", sep=""))
rec = read.table(paste(args[1], ".record", sep=""), sep=",", strip.white=TRUE, header=TRUE)
db = read.table(paste(args[1], ".database", sep=""), sep=",", strip.white=TRUE, header=TRUE)

rec$date <- as.Date(rec$date, "%Y-%m-%d")

head(db)
tail(rec)

str(rec)

rec$bodyweight = na.locf(rec$bodyweight)

plot(bodyweight~date, data=rec)

cl = rainbow(length(db$exercise))
plot(1, type="n", xlab="", ylab="", xlim=c(min(rec$date), max(rec$date)), ylim=c(-50, max(rec$weight, na.rm=TRUE)))
for (i in 1:length(db$exercise)) {
	# print(subset(rec$weight, rec$exercise==db$exercise[i]))
	lines(weight~date, data=rec, subset=(exercise==as.character(db$exercise[i])), col = cl[i], type='b')
}
legend("topleft", legend = db$exercise, col = cl, lwd = 1, cex = 0.5)

cl = rainbow(length(db$exercise))
plot(1, type="n", xlab="", ylab="", xlim=c(min(rec$date), max(rec$date)), ylim=c(0, max(rec$weight + rec$bodyweight, na.rm=TRUE)))
for (i in 1:length(db$exercise)) {
	# print(subset(rec$weight, rec$exercise==db$exercise[i]))
	lines((weight + bodyweight*db$bwratio[i])~date, data=rec, subset=(exercise==as.character(db$exercise[i])), col = cl[i], type='b')
}
legend("topleft", legend = db$exercise, col = cl, lwd = 1, cex = 0.5)


# Now fill plot with the log transformed coverage data from the
# files one by one.
# for(i in 1:length(data)) {
#     lines(density(log(data[[i]]$coverage)), col = cl[i])
#     plotcol[i] <- cl[i]
# }