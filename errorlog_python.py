import time
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def error_log(server):   
    table = []
    
    #must replace domain and folder with your location of the log files
    location = '\\\\\domain\\folder\\logs\\'
    
    primary = server[0:3]
    print(f'{server}')
    try:
        with open(location+primary+'\\'+server+'\\Result.txt') as f:
            for line in f:
                if line.startswith('2021'):
                    data = extract_fields(line)
                    table.append(data)
    except:
        print('failed to open Result.txt file')

    dataframe = pd.DataFrame.from_records(table)
    dataframe.columns = ['date','category','description']

    table = 0
    data = 0
    dataframe['date'] = pd.to_datetime(dataframe['date'])
    dataframe.set_index('date', inplace = True, drop =True)
    dataframe['All Points'] = 1

    #### this looks at error log column that I have called category and counts similar 
    ####occurances into a new dataframe called countdf
    countdf = dataframe.groupby('category').category.count().reset_index(name="count")
    Total = countdf['count'].sum()
    countdf.sort_values(by=['count'],ascending=True, inplace=True)
    countdf = countdf.reset_index(drop=True)
    countdf.loc['Total'] = pd.Series(Total, index=['count'])
    print(countdf.tail(n=10))
    
    return(dataframe)
    

#This will plot the dataframe of the grouped error information
def plot_error(error_data, mean, stadev,start_time,end_time,inter):
    
    #Standard Deviation Multiplier for the total error limit
    stadev_mult = 3
    
    #error limit is the limit for what is considered excessive alarms
    #error data mask replaces the number of errors with true/false, if it exceeds the limit
    #error data mask value is the values of error data mask in true/false
    error_limit = round(mean+stadev*stadev_mult)
    error_data_mask = error_data >= error_limit
    error_data_mask_value = error_data_mask.values  #true/false  
    
    #This just generates a list of the times where we exceeded the error limit
    error_label = error_data_mask[error_data_mask['All Points'] == True]
    error_excess_labels = error_label.index.strftime("%Y-%m-%d %H:%M:%S").tolist()
    
    
    ticks = []
    xlabels = []
    z=-1
    count = 0
    midnightcount = 0 
    
    for x,y in zip(error_data_mask_value,error_data_mask.itertuples()):
        z=z+1
        if count == 0 and midnightcount == 0:
            if x == True:
                xlabels.append(y.Index.strftime("%Y-%m-%d %H:%M:%S"))
                ticks.append(z)
                count = 1    

            elif '00:00:00' in str(y.Index):
                xlabels.append(y.Index.strftime("%Y-%m-%d"))
                ticks.append(z)
                midnightcount = 1
                
        elif count != 0:
            count = count + 1
            #this is how many bars to skips for date/time label
            if count == 5:
                count = 0
                
        elif midnightcount != 0:
            midnightcount = midnightcount + 1
            #this is how many bars to skip at a midnight count
            if midnightcount == 3:
                midnightcount = 0
    
    
    #begin plotting    
    %matplotlib qt
    fig,ax=plt.subplots(figsize=(15,10))
    
    error_data['All Points'].plot(kind = 'bar',
                                  ax=ax, 
                                  #figsize=(40,20), 
                                  color=(error_data['All Points']>mean+stadev*stadev_mult).map({True:'r',
                                                                                    False:'b'}))
    #HORIZONTAL LINES
    #green is the mean
    #orange dashed is the limit for high alarming
    plt.axhline(mean, color='green')
    plt.axhline((mean+stadev*stadev_mult), color='orange',linestyle='dashed')
    
    #plt.ylabel('Number of Errors', fontsize=25)
    #plt.xlabel('Date', fontsize=25)
    plt.ylabel('Number of Errors')
    plt.xlabel('Date')
    
    #set_ylim needs to be automated
    ax.set_xticks(ticks)
    ax.set_xticklabels(xlabels)
    ax.set_title('Error Log Trend from:   '+start_time+'   to   '+end_time +'\n Interval = '+inter+'\n mean = '+str(mean)+'\n Standard Deviation = '+str(stadev))
    
    ylim_max = error_data['All Points'].max()
    ax.set_ylim([0,ylim_max+5])
    
    #plt.tick_params(labelsize=15)
    plt.grid(axis='y')
    plt.tight_layout()
    
    try:
        plt.savefig('image.pdf')
    except:
        print('fail to export pdf')

    return(error_excess_labels)


#this will break up the error logs by the blank spaces
def extract_fields(line):
    parts = line.split(' ', 3)
    return(parts[0].strip()+' '+ parts[1].strip(), parts[2].strip(), parts[3].strip())

#this will group all EXCEPT one point in the category column and sum them by a time interval
def df_without(time, dataframe, point):
    data_wx = dataframe[~dataframe['category'].isin(point)]
    data_wx = data_wx.groupby(pd.Grouper(freq=time)).sum()
    return(data_wx)

#this will group only a certain point in the category column and sum them by a time interval
def df_with(time, dataframe, point):
    data_w = dataframe[dataframe['category'].isin(point)]
    data_w = data_w.groupby(pd.Grouper(freq=time)).sum()
    return(data_w)

#this will group all points in category column and sum them by a time interval
def df_all(time,dataframe):
    data_all = dataframe.groupby(pd.Grouper(freq=time)).sum()
    return(data_all)

#this exports a list of the top error descriptions and their count
def export_error_count(dataframe):    
    countdf = dataframe.groupby('description').description.count().reset_index(name="count")
    countdf.sort_values(by=['count'],ascending=True, inplace=True)
    countdf = countdf.reset_index(drop=True)
    countdf.loc['Total'] = pd.Series(Total, index=['count'])
    countdf.tail(n=10)
    countdf.to_excel("Errorlog_output.xlsx",sheet_name='top_errors', index=False)  
    return(print(f'Top errors exported to "Errorlog_output.xlsx"'))

def error_plot(dataframe, error_include, interval,start_time,end_time,point=['OMNICOMM']):
    if error_include == 'all':
        print('all')
        df_return = df_all(interval,dataframe)
    
    elif error_include == 'with':
        print('with')
        try:
            df_return = df_with(interval, dataframe, point)
        except:
            print(f'Need to define the with tag')
    
    elif error_include == 'without':
        print('without')
        try:
            df_return = df_without(interval, dataframe, point)
        except:
            print(f'Need to define the with tag')        
    
    
    df_return = df_return.loc[start_time:end_time]
    stadev = round(float(df_return.std()),1)
    mean = round(float(df_return.mean()),1)
    #print(mean)
    #print(stadev)
    error_excess_labels = plot_error(df_return,mean,stadev,start_time,end_time,interval)
    
    return("Error log plot")


#RUNNING THE TOOL
#error_plot(dataframe, error_include, interval, point=['OMNICOMM'])
#error_include options are: all, with, without
#interval='10T' T is a minute, H is hour

interval='10T'
start_time = '2021-3-1'
end_time = '2021-3-8'

error_plot(dataframe,'all',interval,start_time,end_time)
#error_plot(dataframe,'with',interval,start_time,end_time,['OMNICOMM'])
#error_plot(dataframe,'without',interval,start_time,end_time,['OMNICOMM', 'ACEEngine_7520'])


