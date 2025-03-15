import pandas as pd
import numpy as np
#import streamlit as st
from scipy.optimize import linprog
import math
path = "D://Downloads//Python Parameterisation//"
file = "Input_Trial_Data - 1.xlsx"
output_file = "Output_Trial_Data - 1.xlsx"
#num machines
df1 = pd.read_excel(path+file, sheet_name="Sheet1")
#tools and capacity per day
df2 = pd.read_excel(path+file, sheet_name="Sheet2")
#monthly requirement
df3 = pd.read_excel(path+file, sheet_name="Sheet3")
#given data for vendors, skus, machines, requirements and tool capacities
vendors = df1["Vendor"].to_list()
skus = df3["SKU"].to_list()
requirements = df3.set_index("SKU")["Requirement"].to_dict()
machines = df1.set_index("Vendor")["No. of m/c"]
#single cavity or multi cavity tool
max_rep_tool = max(df2["Type"].to_list())
tool_count = df2.set_index(["Vendor", "SKU", "Type"])["No."].to_dict()
tool_output = df2.set_index(["Vendor", "SKU", "Type"])["Capacity"].to_dict()
#size of the problem
num_vendors = len(vendors)
num_skus = len(skus)
#empty libraries to store tool data
all_tool_count = {}
all_tool_output = {}
sku_type = {}
for i, vendor in enumerate(vendors):
    for j, sku in enumerate(skus):
        for k in range(max_rep_tool):
            if (vendor, sku, k+1) in tool_count:
                all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)] = tool_count[(vendor, sku, k+1)]*24   #change 24 to number of working days
                all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(k+1)] = tool_output[(vendor, sku, k+1)]
                sku_type[str(sku)+"-"+str(k+1)] = sku
            else:
                all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)] = 0
                all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(k+1)] = 0
                sku_type[str(sku)+"-"+str(k+1)] = sku
    machines[vendor] = machines[vendor]*24   #change 24 to number of working days
size = (num_skus*max_rep_tool)*num_vendors
#objective function
#Max z = 150*x1+200*x2+0*x3.............
#x1, x2, x3...... are the number of tools used per sku per vendor per day
z = []
for i, vendor in enumerate(vendors):
    for j, sku, in enumerate(skus):
        for k in range(max_rep_tool):
            z.append((-1)*all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(k+1)])
#empty matrix for constraints
A_ub = []
b_ub = []
A_ub_temp = []
x_bounds = []
#machine constraints
#total number of tools for all skus used by each vendor per day must be less than or equal to the total number of machines available per day
#number of inequalities is equal to the number of vendors
for i, vendor in enumerate(vendors):
    row1 = [0]*(size)
    for j, sku in enumerate(skus):
        for k in range(max_rep_tool):
            if (vendor, sku, k+1) in tool_count:
                row1[i*num_skus*max_rep_tool+j*max_rep_tool+k] = 1
    A_ub.append(row1)
    b_ub.append(int(machines[vendor]))
#tool constraints for each vendor, sku, and type of tool
#number of tools used for each sku by each vendor should be less than the number of tools available per day
#number of inequalities is equal to the size variable (num_vendors*max_rep_tool*num_vendors)
for i, vendor in enumerate(vendors):
    for j, sku in enumerate(skus):
        for k in range(max_rep_tool):
            row2 = [0]*(size)
            if (vendor, sku, k+1) in tool_count:
                row2[i*num_skus*max_rep_tool+j*max_rep_tool+k] = 1
            A_ub.append(row2)
            b_ub.append(int(all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)]))
#requirements
#total production must not exceed the requirement
#number of inequalities is equal to the number of skus
for i, sku in enumerate(skus):
    for j  in range(max_rep_tool):
        row3 = [0]*(size)
        for k, vendor in enumerate(vendors):
            if (vendor, sku, j+1) in tool_count:
                row3[k*num_skus*max_rep_tool+i*max_rep_tool+j] = int(all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(j+1)])
        A_ub_temp.append(row3)
    b_ub.append(requirements[sku])
for i in range(len(A_ub_temp)):
    if i%2 == 0:
        row4 = [0]*len(A_ub_temp[0])
        for j in range(len(A_ub_temp[0])):
            row4[j] = A_ub_temp[i][j]+A_ub_temp[i+1][j]
        A_ub.append(row4)
#limits for x (>=0)
#number of inequalities is equal to the size variable (num_vendors*max_rep_tool*num_vendors)
for i, vendor in enumerate(vendors):
    for j, sku in enumerate(skus):
        for k in range(max_rep_tool):
            if (vendor, sku, k+1) in tool_count:
                x_bounds.append((0, None))
            else:
                x_bounds.append((0, 0))
#solution
soln1 = linprog(z, A_ub=A_ub, b_ub=b_ub, bounds=x_bounds, method="simplex")
print(soln1)
optimal_x = soln1.x.reshape(num_vendors, max_rep_tool*num_skus)
#post processing
#per sku
fulfilled_net = []
#per sku per type
fulfilled = []
tools_left = []
#per machine
num_machines_used = {}
num_machines_left = {}
#per sku
skuwise_fulfilled = {}
skuwise_remaining = {}
net_fulfilled = {}
#per vendor per sku
available_tools = {}
unused_tools = {}
max_output_per_sku = {}
for i, vendor in enumerate(vendors):
    #fulfilled orders
    temp = 0
    #tools left
    temp1 = 0
    #machines used
    temp2 = 0
    for j, sku in enumerate(skus):
        for k in range(max_rep_tool):
            temp = soln1.x[i*num_skus*max_rep_tool+j*max_rep_tool+k]*all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(k+1)]
            temp1 = all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)]-soln1.x[i*num_skus*max_rep_tool+j*max_rep_tool+k]
            temp2 = temp2+(soln1.x[i*num_skus*max_rep_tool+j*max_rep_tool+k])
            if int(temp)%10==9:
                temp = int(temp)+1
            fulfilled.append(int(temp))
            tools_left.append(int(temp1))
    num_machines_used[vendor] = temp2
    #number of machines left
    num_machines_left[vendor] = int(machines[vendor]-num_machines_used[vendor])
#combine total production for each sku using each type of tools
for i in range(len(fulfilled)):
    temp3 = 0
    if i%2==0:
        temp3 = fulfilled[i]+fulfilled[i+1]
        fulfilled_net.append(temp3)
for i, sku in enumerate(skus):
    temp4 = 0
    for j, vendor in enumerate(vendors):
        temp4 = temp4+fulfilled_net[j*num_skus+i]
        net_fulfilled[(vendor, sku)] = fulfilled_net[j*num_skus+i]
    skuwise_fulfilled[sku] = temp4
    skuwise_remaining[sku] = requirements[sku]-skuwise_fulfilled[sku]
    if  skuwise_remaining[sku] == 1:
        skuwise_fulfilled[sku] = skuwise_fulfilled[sku]+1
        skuwise_remaining[sku] = 0
        for j, vendor in enumerate(vendors):
            if net_fulfilled[(vendor, sku)]%10 == 9:
                net_fulfilled[(vendor, sku)] = net_fulfilled[(vendor, sku)]+1
#output df
data_final = []
for i, sku in enumerate(skus):
    data = {
    "SKU": sku,
    "Demand": requirements[sku],
    "Achievable": skuwise_fulfilled[sku],
    "Remaining": skuwise_remaining[sku],
    }
    for j, vendor in enumerate(vendors):
        data[vendor] = net_fulfilled[(vendor, sku)]
    data_final.append(data)
df_output = pd.DataFrame(data_final)
#max capacity for each vendor(unused)
#max tool_capapcity*tool_count+next max tool_capacity*tool_count........ upto number of machines
vendor_max_capacity = {}
for vendor in vendors:
    for sku in skus:
        total_capacity = 0
        for k in range(max_rep_tool):
            total_capacity = total_capacity+all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)]*all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(k+1)]
    vendor_max_capacity[vendor] = total_capacity
#maximum possible output of each sku for each vendor
for i, sku in enumerate(skus):
    #max capacity
    temp7 = 0
    for j, vendor in enumerate(vendors):
        #used tools
        temp5 = 0
        #available tools
        temp6 = 0
        for k in range(max_rep_tool):
            temp5 = temp5+(soln1.x[vendors.index(vendor)*num_skus*max_rep_tool+skus.index(sku)*max_rep_tool+k])
            temp6 = temp6+all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)]
            temp7 = temp7+all_tool_count[str(vendor)+"-"+str(sku)+"-"+str(k+1)]*all_tool_output[str(vendor)+"-"+str(sku)+"-"+str(k+1)]
        available_tools[(vendor, sku)] = temp5
        unused_tools[(vendor, sku)] = temp6-temp5
    max_output_per_sku[sku] = int(temp7)
#reason for short production
extra_tools = {}
remarks = []
for sku in skus:
    remark = ""
    allocated_total = skuwise_fulfilled[sku]
    count = 0
    if skuwise_remaining[sku]>0:
        if max_output_per_sku[sku]<requirements[sku] and skuwise_fulfilled[sku] in range(max_output_per_sku[sku]-2, max_output_per_sku[sku]+2):
            remark = "Insufficient Tools"
        else:
            remark = "Insufficient Machines"
    elif skuwise_remaining[sku]<0:
        remark = "Excess production"
    remarks.append(remark)
df_output["Remarks"] = remarks
#max possible production of each vendor
for i, vendor in enumerate(vendors):
    temp0 = 0
    temp_machines = 0
    temp_tools = 0
    temp_capacity = 0
    x = 0
    total_cap = 0
    df_temp = df2[df2.Vendor == vendor]
    df_temp = df_temp.sort_values(by=["Capacity"], ascending=False)
    start = machines[vendor]/24    #replace 24 by the number of working days
    temp_tools = df_temp["No."].values.tolist()
    temp_capacity = df_temp["Capacity"].values.tolist()
    k = 0
    temp10 = 0
    for j, sku in enumerate(skus):
        temp10 = temp10+net_fulfilled[(vendor, sku)]
    df_output.at[num_skus+2, vendor] = temp10
    while(start>0 and k<=len(temp_tools)-1):
        if start>temp_tools[k]:
            x = x+(temp_tools[k]*temp_capacity[k])*24    #replace 24 by the number of working days
        else:
            x = x+(start*temp_capacity[k])*24    #replace 24 by the number of working days
        start = start-temp_tools[k]
        k = k+1
    df_output.at[num_skus+3, vendor] = x
    df_output.at[num_skus+4, vendor] = round((temp10/x)*100, 2)
    total_capacity = total_capacity+x
df_output.at[num_skus+3, "Remarks"] = total_capacity
#total demand, fulfilled numbe and percent achieved
max_per_sku_capacity = {}
percent_tool_utilization = {}
for i, sku in enumerate(skus):
    y = 0
    sum_y = 0
    for j, vendor in enumerate(vendors):
        for k in range(max_rep_tool):
            if (vendor, sku, k+1) in tool_count:
                y = tool_count[(vendor, sku, k+1)]*24*tool_output[(vendor, sku, k+1)]    #replace 24 by the number of working days
                sum_y = sum_y+y
    max_per_sku_capacity[sku] = sum_y
    if sum_y != 0:
        percent_tool_utilization[sku] = round(skuwise_fulfilled[sku]/sum_y*100, 2)
    else:
        percent_tool_utilization[sku] = 0
temp8 = 0
temp9 = 0
for i, sku in enumerate(skus):
    temp8 = temp8+skuwise_fulfilled[sku]
    temp9 = temp9+requirements[sku]
demand_fulfilled = temp8/temp9*100
df_output.at[num_skus+2, "Demand"] = temp9
df_output.at[num_skus+2, "Achievable"] = temp8
df_output.at[num_skus+2, "Remarks"] = temp8
df_output.at[num_skus+3, "Demand"] = "Fulfilled %"
df_output.at[num_skus+3, "Achievable"] = round(demand_fulfilled, 2)
df_output.at[num_skus+4, "Remaining"] = "Utilization %"
df_output.at[num_skus+4, "Remarks"] = round(temp8/total_capacity*100, 2)
df_output["Max SKU Capacity"] = df_output["SKU"].map(max_per_sku_capacity)
df_output["Tool Utilization %"] = df_output["SKU"].map(percent_tool_utilization)
print(df_output)
#df output in excel sheet
writer = pd.ExcelWriter(path+output_file, engine="xlsxwriter")
workbook = writer.book
df_output.to_excel(writer, sheet_name="Optimized Allocation", index=False)
worksheet = writer.sheets["Optimized Allocation"]
print(f"Optimized allocation saved to {output_file}")
#unused vs used tools for each vendor per sku
unused_tools_data = []
for (vendor, sku), unused in unused_tools.items():
    available = available_tools[(vendor, sku)]
    unused_tools_data.append({"Vendor": vendor, "SKU": sku, "Used Tool Hours": available*21/24, "Unused Tool Hours": unused*21/24})    #replace 24 by the number of working days
df_unused_tools = pd.DataFrame(unused_tools_data)
df_unused_tools.to_excel(writer, sheet_name="Tool Data", index=False)
#pivot table
pivot_table = df_unused_tools.pivot_table(index="Vendor", values=["Used Tool Hours", "Unused Tool Hours"], aggfunc="sum")
pivot_table.to_excel(writer, sheet_name="Tool Allocation Pivot")
#run code and drill down pivot using streamlit
#remove comments below and run the following command in the terminal, allow permissions and it will launch streamlit app on chrome
# use : streamlit run "D://Downloads//Python Parameterisation//Opti_problem.py" (replace the path and file name of the python file)
pivot_table = pivot_table.reset_index()
'''st.title("Tool Allocation Pivot Table")
selected_vendor = st.dataframe(pivot_table, use_container_width=True)
selected_vendor = st.selectbox("Select a Vendor to Drill Down:", pivot_table["Vendor"].unique())
if selected_vendor:
    filtered_data = df_unused_tools[df_unused_tools["Vendor"] == selected_vendor]
    st.subheader(f"Details for Vendor: {selected_vendor}")
    st.dataframe(filtered_data)'''
writer.close()