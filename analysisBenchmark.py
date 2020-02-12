import argparse
import re
import glob
import pandas as pd

# import xlsxwriter as xl
# import numpy as  np
# from vincent.colors import brews

# Parser to collect user given arguments
parser = argparse.ArgumentParser(prog="analysisBenchmark", description='Extract the results from the output files.')
parser.add_argument('-p', '--path', metavar='path', type=str, help="Path to folder results", required=True, nargs='+')
parser.add_argument('-c', '--config', metavar='path', type=str, help="Config file", required=True, nargs='+')
args = parser.parse_args()

expectedOutput = []
# Parse config file
config_file = open(" ".join(args.config), "r")
while True:
	line = config_file.readline()
	if not line:
		break
	parseType = re.search("(.*?)\=", line)
	if parseType != None:
		parseType = parseType.group(0)
		if parseType == "FILE=":
			fileConvention = str(args.path[0]) + str(config_file.readline())
		elif parseType == "OUTPUT=":
			while True:
				outputLine = config_file.readline()
				if not outputLine:
					break
				if re.search("\[(.*?)\]", outputLine) != None:
					expectedOutput.append(outputLine)
			break

fileNameVars = re.findall(r"\[(.*?)\]", fileConvention) +  ['target', 'object of study', 'core performance level', 'core frequency', 'core voltage', 'memory performance level', 'memory frequency', 'memory voltage']

while True:
	match =  re.search(r"\[(.*?)\]", fileConvention)
	if match == None:
		break
	fileConvention = fileConvention[0 : match.span()[0] : ] + "(.*?)" + fileConvention[match.span()[1] : :]

outputNameVars = []
for idx, line in enumerate(expectedOutput):
	match =  re.search(r"\[(.*?)\]", line)
	outputNameVars.append(match.groups()[0])
	expectedOutput[idx] = line[0 : match.span()[0] : ] + "(.*?)" + line[match.span()[1] : :]

# Get all the files on the results folder
files = [f for f in glob.glob(args.path[0] + "/*.txt", recursive=True)]

Benchmark = {}

numberOfExecutions = 0

for f in files:	
	regex = re.compile(fileConvention[:-1] + "-")
	benchmarkType = []
	for i in regex.match(f).groups():
		benchmarkType.append(i)
	benchmarkType = "-".join(benchmarkType)

	regex = re.compile(fileConvention[:-1] + "-(.*?)-(.*?)-Core-(.*?)-(.*?)-(.*?)-Memory-(.*?)-(.*?)-(.*?).txt")
	fileNameValues = []
	for i in regex.match(f).groups():
		try:
			fileNameValues.append(int(i))
		except:
			fileNameValues.append(i)
	params = dict(zip(fileNameVars, fileNameValues))

	with open(f, "r") as search:
		for idx, regex in enumerate(expectedOutput):
			numberOfExecutions = 0
			regexx = re.compile(regex)
			for line in search:
				value = regexx.search(line)
				if value != None:
					value = value.group()
					for word in regex.split(" "):
						value = value.replace(word, "")
					try:
						params[outputNameVars[idx] + " " + str(numberOfExecutions)] = float(value)
					except:
						value = value.replace("\n", "")
						params[outputNameVars[idx] + " " + str(numberOfExecutions)] = value.replace(" ", "")
					numberOfExecutions = numberOfExecutions + 1
			search.seek(0)

	if benchmarkType not in Benchmark:
		Benchmark[benchmarkType] = []

	Benchmark[benchmarkType].append(params)


order = ['core performance level', 'core frequency', 'core voltage', 'memory performance level', 'memory frequency', 'memory voltage']
for value in outputNameVars:
	for i in range(numberOfExecutions):
		order.append(value + " " + str(i))

# Create a Pandas Excel writer using XlsxWriter as the engine.
excel_file = "./" + str(args.path[0]) + 'results.xlsx'
sheet_name = 'Data'

writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')

Benchmark_dt = {}
for key, value in Benchmark.items():
	Benchmark_dt[key] = pd.DataFrame.from_dict(Benchmark[key])
	Benchmark_dt[key] = Benchmark_dt[key][order]
	Benchmark_dt[key].sort_values(by=['core performance level', 'core frequency', 'core voltage', 'memory performance level', 'memory frequency', 'memory voltage'], ascending=[True, False, False, True, False, False] ,inplace=True)
	Benchmark_dt[key].dropna(inplace=True)

	print(Benchmark_dt[key])

	Benchmark_dt[key].to_excel(writer, sheet_name=str(key))

writer.save()
exit()

# Adds delta computation
# result_dt['delta_accuracy'] = np.nan
# result_dt['delta_max_power'] = np.nan
# result_dt['delta_avg_power'] = np.nan
# result_dt['delta_energy'] = np.nan
# result_dt['delta_time'] = np.nan

# cur_level = -1
# default_time = 0
# default_acc = 0
# default_max_power = 0
# default_avg_power = 0
# default_energy = 0

# for index, row in result_dt.iterrows():
# 	if cur_level == row['LEVEL']:
# 		result_dt.at[index, 'delta_accuracy'] = ((row['accuracy19'] - default_acc)/default_acc)*100
# 		result_dt.at[index, 'delta_max_power'] = ((row['Max Power [W]'] - default_max_power)/default_max_power)*100
# 		result_dt.at[index, 'delta_avg_power'] = ((row['Average Power [W]'] - default_avg_power)/default_avg_power)*100
# 		result_dt.at[index, 'delta_energy'] = ((row['Energy [J]'] - default_energy)/default_energy)*100
# 		result_dt.at[index, 'delta_time'] = ((row['tot_times19'] - default_time)/default_time)*100
# 	else:
# 		cur_level = row['LEVEL']
# 		default_time = row['tot_times19']
# 		default_acc = row['accuracy19']
# 		default_max_power = row['Max Power [W]']
# 		default_avg_power = row['Average Power [W]']
# 		default_energy = row['Energy [J]']

# 		result_dt.at[index, 'delta_accuracy'] = 0
# 		result_dt.at[index, 'delta_max_power'] = 0
# 		result_dt.at[index, 'delta_avg_power'] = 0
# 		result_dt.at[index, 'delta_energy'] = 0
# 		result_dt.at[index, 'delta_time'] = 0

# 	result_dt.at[index, 'delta acc 0'] = ((row['acc 0'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 1'] = ((row['acc 1'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 2'] = ((row['acc 2'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 3'] = ((row['acc 3'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 4'] = ((row['acc 4'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 5'] = ((row['acc 5'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 6'] = ((row['acc 6'] - row['accuracy19'])/row['accuracy19'])*100
# 	result_dt.at[index, 'delta acc 7'] = ((row['acc 7'] - row['accuracy19'])/row['accuracy19'])*100




# Count the number of entries per level
# numberOfEntries = np.zeros(8)
# for i in range(0,8):
# 	numberOfEntries[i] = len(result_dt[result_dt['LEVEL'] == i])






# Access the XlsxWriter workbook and worksheet objects from the dataframe.
workbook = writer.book
worksheet = writer.sheets[sheet_name]

actual_line = 2

# Run all performance values
for i in range(0,8):
	nameF = result_dt.iloc[actual_line-2, 1]

	########### TIME CHART ################

	# Create a chart to represent the total training time
	time_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	time_chart.add_series({
		'name':       'LEVEL ' + str(i) + ', FREQ ' + str(nameF) + ' MHz',
		'values':     '=' + str(sheet_name) + '!$BL$' + str(actual_line) + ':$BL$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	time_chart.set_title ({'name': 'Time to Train:'})
	time_chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	time_chart.set_y_axis({'name': 'Time [s]',
					  'major_gridlines': {'visible': True}, 'min': 256, 'max': 270})									   
	# Insert the chart into the worksheet.
	worksheet.insert_chart('A280', time_chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	########### Delta TIME CHART ################

	# Create a chart to represent the total training time
	time_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	time_chart.add_series({
		'name':       'LEVEL ' + str(i) + ', FREQ ' + str(nameF) + ' MHz',
		'values':     '=' + str(sheet_name) + '!$EI$' + str(actual_line) + ':$EI$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	time_chart.set_title ({'name': 'Delta Time to Train:'})
	time_chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	time_chart.set_y_axis({'name': 'Delta Time [%]',
					  'major_gridlines': {'visible': True}, 'min': -4, 'max': 3})				
	#				   
	# Insert the chart into the worksheet.
	worksheet.insert_chart('A303', time_chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})


	########### Power CHART ################

	# Create a chart object.
	power_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	power_chart.add_series({
		'name':       'MAX POWER',
		'values':     '=' + str(sheet_name) + '!$BN$' + str(actual_line) + ':$BN$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the series of the chart from the dataframe data.
	power_chart.add_series({
		'name':       'AVG POWER',
		'values':     '=' + str(sheet_name) + '!$BM$' + str(actual_line) + ':$BM$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	power_chart.set_title ({'name': 'MAX and AVG POWER'})
	power_chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	power_chart.set_y_axis({'name': 'Power [W]',
					  'major_gridlines': {'visible': True}, 'min': 0, 'max': 120})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A187', power_chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	########### Delta MAX and AVG Power CHART ################

	# Create a chart object.
	power_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	power_chart.add_series({
		'name':       'MAX POWER',
		'values':     '=' + str(sheet_name) + '!$EF$' + str(actual_line) + ':$EF$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the series of the chart from the dataframe data.
	power_chart.add_series({
		'name':       'AVG POWER',
		'values':     '=' + str(sheet_name) + '!$EG$' + str(actual_line) + ':$EG$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	power_chart.set_title ({'name': 'Delta MAX and AVG POWER'})
	power_chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	power_chart.set_y_axis({'name': 'Power [W]',
					  'major_gridlines': {'visible': True}, 'min': -60, 'max': 80})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A210', power_chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})


	########### ENERGY CHART ################

	# Create a chart object.
	energy_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	energy_chart.add_series({
		'name':       'ENERGY',
		'values':     '=' + str(sheet_name) + '!$BO$' + str(actual_line) + ':$BO$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	energy_chart.set_title ({'name': 'ENERGY'})
	energy_chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	energy_chart.set_y_axis({'name': 'Energy [J]',
					  'major_gridlines': {'visible': True}, 'min': 3500, 'max': 15000})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A233', energy_chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	########### Delta ENERGY CHART ################

	# Create a chart object.
	energy_chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	energy_chart.add_series({
		'name':       'ENERGY',
		'values':     '=' + str(sheet_name) + '!$EH$' + str(actual_line) + ':$EH$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	energy_chart.set_title ({'name': 'Delta ENERGY'})
	energy_chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	energy_chart.set_y_axis({'name': 'Delta Energy [%]',
					  'major_gridlines': {'visible': True}, 'min': -30, 'max': 30})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A256', energy_chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	########### Delta Accuracy CHART ################

	# Create a chart object.
	chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	chart.add_series({
		'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
		'values':     '=' + str(sheet_name) + '!$EE$' + str(actual_line) + ':$EE$' + str(actual_line + int(numberOfEntries[i]) - 1),
		'categories': '=' + str(sheet_name) + '!$D$' + str(actual_line) + ':$D$'+ str(actual_line + int(numberOfEntries[i]) - 1),
	})

	# Configure the chart axes.
	chart.set_title ({'name': 'Delta Accuracy'})
	chart.set_x_axis({'name': 'Voltage [mV]', 'min': 800, 'max': 1200})
	chart.set_y_axis({'name': 'Delta Accuracy [%]',
					  'major_gridlines': {'visible': True}, 'min': -0.1, 'max': 0.1})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A165', chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	########### Accuracy CHART ################

	# Create a chart object.
	chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Configure the series of the chart from the dataframe data.
	for a in range(int(numberOfEntries[i])):
		chart.add_series({
			'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
			'values':     '=' + str(sheet_name) + '!$E$' + str(actual_line) + ':$X$' + str(actual_line),
			'categories': '=' + str(sheet_name) + '!$AS$' + str(actual_line) + ':$BL$'+ str(actual_line),
		})
		actual_line += 1

	# Configure the chart axes.
	chart.set_title ({'name': 'LEVEL ' + str(i) + ', FREQ ' + str(nameF) + ' MHz'})
	chart.set_x_axis({'name': 'Time [s]'})
	chart.set_y_axis({'name': 'Accuracy [%]',
					  'major_gridlines': {'visible': True}, 'min': 0, 'max': 100})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A142', chart, {'x_offset': i*750, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})
	



actual_line = 2

for i in range(0,8):
	nameF = result_dt.iloc[actual_line-2, 1]
	worksheet = workbook.add_worksheet("Level" + str(i))
	for j in range(0,8):
		worksheet.write(0,j,j)
	########### Accuracy CHART ################

	# Create a chart object.
	chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	delta_accuracy = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	########### Power CHART ################

	# Create a chart object.
	avgpowerchart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	# Create a chart object.
	maxpowerchart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})

	########### Energy CHART ################

	# Create a chart object.
	enerychart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})


	# Configure the series of the chart from the dataframe data.
	for a in range(int(numberOfEntries[i])):
		chart.add_series({
			'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
			'values':     '=' + str(sheet_name) + '!$CA$' + str(actual_line) + ':$CH$' + str(actual_line),
			'categories': '=Level' + str(i) + '!$A$1:$H$1'
		})

		delta_accuracy.add_series({
			'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
			'values':     '=' + str(sheet_name) + '!$EJ$' + str(actual_line) + ':$EQ$' + str(actual_line),
			'categories': '=Level' + str(i) + '!$A$1:$H$1'
		})

		avgpowerchart.add_series({
			'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
			'values':     '=' + str(sheet_name) + '!$CQ$' + str(actual_line) + ':$CX$' + str(actual_line),
			'categories': '=Level' + str(i) + '!$A$1:$H$1'
		})
		maxpowerchart.add_series({
			'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
			'values':     '=' + str(sheet_name) + '!$CY$' + str(actual_line) + ':$DF$' + str(actual_line),
			'categories': '=Level' + str(i) + '!$A$1:$H$1'
		})

		enerychart.add_series({
			'name':       '=' + str(sheet_name) + '!$D$' + str(actual_line),
			'values':     '=' + str(sheet_name) + '!$DG$' + str(actual_line) + ':$DN$' + str(actual_line),
			'categories': '=Level' + str(i) + '!$A$1:$H$1'
		})
		actual_line += 1

	# Configure the chart axes.
	chart.set_title ({'name': 'LEVEL ' + str(i) + ', FREQ ' + str(nameF) + ' MHz'})
	chart.set_x_axis({'name': 'Performance Level', 'min': 0, 'max': 7})
	chart.set_y_axis({'name': 'Accuracy [%]',
					  'major_gridlines': {'visible': True}, 'min': 98, 'max': 100})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A1', chart, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	# Configure the chart axes.
	delta_accuracy.set_title ({'name': 'Delta Accuracy'})
	delta_accuracy.set_x_axis({'name': 'Performance Level', 'min': 0, 'max': 7})
	delta_accuracy.set_y_axis({'name': 'Delta Accuracy [%]',
					  'major_gridlines': {'visible': True}, 'min': -0.1, 'max': 0.1})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('M1', delta_accuracy, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	# Configure the chart axes.
	avgpowerchart.set_title ({'name': 'AVG POWER'})
	avgpowerchart.set_x_axis({'name': 'Performance Level', 'min': 0, 'max': 7})
	avgpowerchart.set_y_axis({'name': 'Power [W]',
					  'major_gridlines': {'visible': True}})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A24', avgpowerchart, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	# Configure the chart axes.
	maxpowerchart.set_title ({'name': 'MAX POWER}'})
	maxpowerchart.set_x_axis({'name': 'Performance Level', 'min': 0, 'max': 7})
	maxpowerchart.set_y_axis({'name': 'Power [W]',
					  'major_gridlines': {'visible': True}})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A47', maxpowerchart, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})

	# Configure the chart axes.
	enerychart.set_title ({'name': 'Energy'})
	enerychart.set_x_axis({'name': 'Performance Level', 'min': 0, 'max': 7})
	enerychart.set_y_axis({'name': 'Energy [J]',
					  'major_gridlines': {'visible': True}})

	# Insert the chart into the worksheet.
	worksheet.insert_chart('A70', enerychart, {'x_offset': 0, 'y_offset': 0, 'x_scale': 1.5, 'y_scale': 1.5})


# Close the Pandas Excel writer and output the Excel file.
writer.save()
