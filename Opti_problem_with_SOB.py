import pandas as pd
from operator import itemgetter
from scipy.optimize import linprog
import numpy as np
from collections import defaultdict
path = "F://Python trials//Ref Files//"
input_sheet = "New_Input_Trial_Data_Feb.xlsx"
output_sheet = "New_New_Output_Trial_Data_Feb.xlsx"
df1 = pd.read_excel(path+input_sheet, "Sheet1")
df2 = pd.read_excel(path+input_sheet, "Sheet2")
df3 = pd.read_excel(path+input_sheet, "Sheet3")
df4 = pd.read_excel(path+input_sheet, "Sheet4")
working_days = 25
machines_lib = df1.set_index("Vendor")["No. of m/c"].to_dict()
tool_capacity_lib = df2.set_index(["Vendor", "SKU", "Type"])["Capacity"].to_dict()
tools_list = df2.set_index(["Vendor", "SKU", "Type"])["No."].to_dict()
plant_wise_reqs_lib = df3.set_index(["Plant", "SKU"])["Requirement"].to_dict()
sob_lib = df4.set_index(["Vendor", "SKU", "Plant"])["SOB"].to_dict()
net_sku_requirement = df3.groupby("SKU")["Requirement"].sum().to_dict()
vendor_list = df1["Vendor"].to_list()
sku_list = list(set(df3["SKU"].to_list()))
plants_list = list(set(df3["Plant"].to_list()))
max_tool_reps = max(df2["Type"].to_list())
num_skus = len(sku_list)
num_vendors = len(vendor_list)
all_tool_capacity_lib = {}
total_machines_lib = {}
total_tool_capacity_lib = {}
for i, vendor in enumerate(vendor_list):
    for j, sku in enumerate(sku_list):
        for k, plant in enumerate(plants_list):
            for l in range(max_tool_reps):
                if vendor not in machines_lib:
                    machines_lib["Vendor"] = 0
                if (vendor, sku, l+1) not in tool_capacity_lib:
                    tool_capacity_lib[(vendor, sku, l+1)] = 0
                    tools_list[(vendor, sku, l+1)] = 0
                    all_tool_capacity_lib[(vendor, sku, l+1)] = 0
                if (plant, sku) not in plant_wise_reqs_lib:
                    plant_wise_reqs_lib[(plant, sku)] = 0
                all_tool_capacity_lib[(vendor, sku, l+1)] = tool_capacity_lib[(vendor, sku, l+1)]*tools_list[(vendor, sku, l+1)]*25
    total_machines_lib[vendor] = machines_lib[vendor]*working_days
for vendor in vendor_list:
    for sku in sku_list:
        for i in range(max_tool_reps):
                if (vendor, sku) not in total_tool_capacity_lib:
                    total_tool_capacity_lib[(vendor, sku)] = 0
                total_tool_capacity_lib[(vendor, sku)] = total_tool_capacity_lib[(vendor, sku)]+all_tool_capacity_lib[(vendor, sku, i+1)]
size = (num_skus*max_tool_reps)*num_vendors
alloc_req = 0
vendor_wise_req = {}
for plant in plants_list:
    for sku in sku_list:
        plant_sku_req = plant_wise_reqs_lib[(plant, sku)]
        for vendor in vendor_list:
            alloc_req = sob_lib[(vendor, sku, plant)]*plant_sku_req
            if (vendor, sku) not in vendor_wise_req:
                vendor_wise_req[(vendor, sku)] = 0
            vendor_wise_req[(vendor, sku)] = vendor_wise_req[(vendor, sku)]+alloc_req
z = []
for i, vendor in enumerate(vendor_list):
    for j, sku, in enumerate(sku_list):
        for k in range(max_tool_reps):
            z.append(-1*tool_capacity_lib[(vendor, sku, k+1)])
A_ub = []
b_ub = []
x_bounds = []
for i, vendor in enumerate(vendor_list):
    row1 = [0]*(size)
    for j, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            if (vendor, sku, k+1) in tools_list:
                row1[i*num_skus*max_tool_reps+j*max_tool_reps+k] = 1
    A_ub.append(row1)
    b_ub.append(int(machines_lib[vendor])*working_days)
for i, vendor in enumerate(vendor_list):
    for j, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            row2 = [0]*(size)
            if (vendor, sku, k+1) in tools_list:
                row2[i*num_skus*max_tool_reps+j*max_tool_reps+k] = 1
            A_ub.append(row2)
            b_ub.append(tools_list[(vendor, sku, k+1)]*working_days)
for i, vendor in enumerate(vendor_list):
    for j, sku in enumerate(sku_list):
        row3 = [0]*size
        for k in range(max_tool_reps):
            row3[j*max_tool_reps+i*num_skus*max_tool_reps+k] = 1*tool_capacity_lib[(vendor, sku, k+1)]
        A_ub.append(row3)
        b_ub.append(vendor_wise_req[(vendor, sku)])
for j, vendor in enumerate(vendor_list):
    for i, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            if (vendor, sku, k+1) in tools_list:
                x_bounds.append((0, None))
            else:
                x_bounds.append((0, 0))
soln1 = linprog(z, A_ub=A_ub, b_ub=b_ub, bounds=x_bounds, method="highs")
print(soln1.x)
tools_used = {}
machines_used = {}
net_allocated = {}
net_allocated_merged = {}
vendor_plant_sku_allocation = {}
remaining_machines = {}
remaining_tools = {}
for i, vendor in enumerate(vendor_list):
    temp = 0
    for j, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            tools_used[(vendor, sku, k+1)] = float(soln1.x[j*max_tool_reps+i*num_skus*max_tool_reps+k])
            temp = temp+float(soln1.x[i*num_skus*max_tool_reps+j*max_tool_reps+k])
            net_allocated[(vendor, sku, k+1)] = float(soln1.x[j*max_tool_reps+i*num_skus*max_tool_reps+k])*tool_capacity_lib[(vendor, sku, k+1)]
            remaining_tools[(vendor, sku, k+1)] = int(tools_list[(vendor, sku, k+1)]-tools_used[(vendor, sku, k+1)]/working_days)
            if (vendor, sku) not in net_allocated_merged:
                net_allocated_merged[(vendor, sku)] = 0
            net_allocated_merged[(vendor, sku)] = net_allocated_merged[(vendor, sku)]+net_allocated[(vendor, sku, k+1)]
    machines_used[vendor] = temp/working_days
    remaining_machines[vendor] = int(machines_lib[vendor]-machines_used[vendor])
fulfilled_plant_sku = defaultdict(float)
net_final_lib = {}
plant_wise_remaining = {}
net_remaining = {}
reason1_lib = {}
for vendor in vendor_list:
    for sku in sku_list:
        for plant in plants_list:
            sob = sob_lib[(vendor, sku, plant)]
            plant_req = plant_wise_reqs_lib[(plant, sku)]
            alloc_qty = plant_req*sob
            if alloc_qty>0:
                processed = net_allocated_merged[(vendor, sku)]
                alloc_final = min(alloc_qty, processed)
                vendor_plant_sku_allocation[(vendor, sku, plant)] = alloc_final
                fulfilled_plant_sku[(plant, sku)] = fulfilled_plant_sku[(plant, sku)]+alloc_final
                net_allocated_merged[(vendor, sku)] = net_allocated_merged[(vendor, sku)]-alloc_final
                if (vendor, sku, plant) not in net_final_lib:
                    net_final_lib[(vendor, sku, plant)] = 0
                    net_final_lib[(vendor, sku, plant)] = net_final_lib[(vendor, sku, plant)]+alloc_final
                else:
                    net_final_lib[(vendor, sku, plant)] = net_final_lib[(vendor, sku, plant)]+alloc_final
                plant_wise_remaining[(plant, sku)] = plant_wise_reqs_lib[(plant, sku)]-fulfilled_plant_sku[(plant, sku)]
            if (plant, sku) not in plant_wise_remaining:
                plant_wise_remaining[(plant, sku)] = 0
            if plant_wise_remaining[(plant, sku)]>0 and remaining_machines[vendor]==0:
                reason1_lib[((plant, sku))] = "Insufficient Machines"
            elif plant_wise_remaining[(plant, sku)]>0:
                reason1_lib[((plant, sku))] = "Insufficient Tools"
            elif plant_wise_remaining[(plant, sku)]<0:
                reason1_lib[((plant, sku))] = "Overproduction"
            else:
                reason1_lib[((plant, sku))] = "Requirement Fulfilled"
            if (vendor, sku, plant) not in net_final_lib:
                net_final_lib[(vendor, sku, plant)] = 0
net_final_lib = dict(sorted(net_final_lib.items()))
merged_reason_remaining1 = {}
for key in reason1_lib.keys() & plant_wise_remaining.keys():
    merged_reason_remaining1[key] = (str(plant_wise_remaining[key]), reason1_lib[key])
for sku in sku_list:
    net_remaining[sku] = 0
    for plant in plants_list:
        if (plant, sku) in plant_wise_remaining:
            net_remaining[sku] = net_remaining[sku]+plant_wise_remaining[(plant, sku)]
merged_reason_remaining1 = dict(sorted(merged_reason_remaining1.items()))
z2 = []
for i, vendor in enumerate(vendor_list):
    for j, sku, in enumerate(sku_list):
        for k in range(max_tool_reps):
            z2.append(-1*tool_capacity_lib[(vendor, sku, k+1)])
A_ub2 = []
b_ub2 = []
A_ub_temp = []
x_bounds2 = []
for i, vendor in enumerate(vendor_list):
    row4 = [0]*(size)
    for j, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            if (vendor, sku, k+1) in tools_list:
                row4[i*num_skus*max_tool_reps+j*max_tool_reps+k] = 1
    A_ub2.append(row4)
    b_ub2.append(int(remaining_machines[vendor])*working_days)
for i, vendor in enumerate(vendor_list):
    for j, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            row5 = [0]*(size)
            if (vendor, sku, k+1) in tools_list:
                row5[i*num_skus*max_tool_reps+j*max_tool_reps+k] = 1
            A_ub2.append(row5)
            b_ub2.append(remaining_tools[(vendor, sku, k+1)]*working_days)
for j, sku in enumerate(sku_list):
    row6 = [0]*size
    for i, vendor in enumerate(vendor_list):
        for k in range(max_tool_reps):
            row6[k+num_skus*max_tool_reps*i+j*max_tool_reps] = 1*tool_capacity_lib[(vendor, sku, k+1)]
            print(k+num_skus*max_tool_reps*i+j*max_tool_reps)
    A_ub2.append(row6)
for key, value in net_remaining.items():
    b_ub2.append(float(value))
for j, vendor in enumerate(vendor_list):
    for i, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            if (vendor, sku, k+1) in tools_list:
                x_bounds2.append((0, None))
            else:
                x_bounds2.append((0, 0))
soln2 = linprog(z2, A_ub=A_ub2, b_ub=b_ub2, bounds=x_bounds2, method="highs")
print(soln2.x)
net_tools_used = {}
net_machines_used = {}
net_net_allocated = {}
new_net_allocated = {}
new_net_allocated_merged = {}
net_net_allocated_merged = {}
for i, vendor in enumerate(vendor_list):
    temp2 = 0
    for j, sku in enumerate(sku_list):
        for k in range(max_tool_reps):
            net_tools_used[(vendor, sku, k+1)] = float(soln1.x[j*max_tool_reps+i*num_skus*max_tool_reps+k])+float(soln2.x[j*max_tool_reps+i*num_skus*max_tool_reps+k])
            temp2 = temp2+float(soln1.x[i*num_skus*max_tool_reps+j*max_tool_reps+k])+float(soln2.x[i*num_skus*max_tool_reps+j*max_tool_reps+k])
            net_net_allocated[(vendor, sku, k+1)] = (float(soln1.x[j*max_tool_reps+i*num_skus*max_tool_reps+k])+float(soln2.x[j*max_tool_reps+i*num_skus*max_tool_reps+k]))*tool_capacity_lib[(vendor, sku, k+1)]
            new_net_allocated[(vendor, sku, k+1)] = float(soln2.x[j*max_tool_reps+i*num_skus*max_tool_reps+k])*tool_capacity_lib[(vendor, sku, k+1)]
            remaining_tools[(vendor, sku, k+1)] = int(tools_list[(vendor, sku, k+1)]-net_tools_used[(vendor, sku, k+1)]/working_days)
            if (vendor, sku) not in net_net_allocated_merged:
                net_net_allocated_merged[(vendor, sku)] = 0
            if (vendor, sku) not in new_net_allocated_merged:
                new_net_allocated_merged[(vendor, sku)] = 0
            net_net_allocated_merged[(vendor, sku)] = net_net_allocated_merged[(vendor, sku)]+net_net_allocated[(vendor, sku, k+1)]
            new_net_allocated_merged[(vendor, sku)] = new_net_allocated_merged[(vendor, sku)]+new_net_allocated[(vendor, sku, k+1)]
    net_machines_used[vendor] = temp2/working_days
    remaining_machines[vendor] = int(machines_lib[vendor]-net_machines_used[vendor])
net_net_final_lib = defaultdict(float)
net_plant_wise_remaining = {}
reason2_lib = {}
merged_reason_remaining2 = {}
for vendor in vendor_list:
    for sku in sku_list:
        for plant in plants_list:
            additional = 0
            if (plant, sku) in plant_wise_remaining and plant_wise_remaining[(plant, sku)]>0:
                if (plant, sku) not in net_plant_wise_remaining:
                    net_plant_wise_remaining[(plant, sku)] = plant_wise_remaining[(plant, sku)]
                additional = min(new_net_allocated_merged[(vendor, sku)], plant_wise_remaining[(plant, sku)])
                new_net_allocated_merged[(vendor, sku)] = new_net_allocated_merged[(vendor, sku)]-additional
                net_net_final_lib[(vendor, sku, plant)] = net_net_final_lib[(vendor, sku, plant)]+additional
                net_plant_wise_remaining[(plant, sku)] = net_plant_wise_remaining[(plant, sku)]-additional
            if (vendor, sku, plant) in net_final_lib:
                net_net_final_lib[(vendor, sku, plant)] = net_net_final_lib[(vendor, sku, plant)]+net_final_lib[(vendor, sku, plant)]
            else:
                net_net_final_lib[(vendor, sku, plant)] = 0
            if (plant, sku) not in net_plant_wise_remaining:
                net_plant_wise_remaining[(plant, sku)] = 0
            if net_plant_wise_remaining[(plant, sku)]>0 and remaining_machines[vendor]==0:
                reason2_lib[((plant, sku))] = "Insufficient Machines"
            elif net_plant_wise_remaining[(plant, sku)]>0:
                reason2_lib[((plant, sku))] = "Insufficient Tools"
            elif net_plant_wise_remaining[(plant, sku)]<0:
                reason2_lib[((plant, sku))] = "Overproduction"
            else:
                reason2_lib[((plant, sku))] = "Requirement Fulfilled"
for key in reason2_lib.keys() & net_plant_wise_remaining.keys():
    merged_reason_remaining2[key] = (str(net_plant_wise_remaining[key]), reason2_lib[key])
net_net_final_lib = dict(sorted(net_net_final_lib.items()))
merged_reason_remaining2 = dict(sorted(merged_reason_remaining2.items()))
net_final_lib_df = pd.DataFrame([
    {"Vendor": k[0], "SKU": k[1], "Plant": k[2], "Allocated Orders": v}
    for k, v in net_final_lib.items()
])
merged_reason_remaining1_df = pd.DataFrame([
    {"Plant": k[0], "SKU": k[1], "Remaining": v[0], "Reason": v[1]}
    for k, v in merged_reason_remaining1.items()
])
net_net_final_lib_df = pd.DataFrame([
    {"Vendor": k[0], "SKU": k[1], "Plant": k[2], "Allocated Orders": v}
    for k, v in net_net_final_lib.items()
])
remaining_machines_df = pd.DataFrame([
    {"Vendor": k, "Machines": v}
    for k, v in remaining_machines.items()
])
remaining_tools_df = pd.DataFrame([
    {"Vendor": k[0], "SKU": k[1], "Tools Used": v}
    for k, v in remaining_tools.items()
])
merged_reason_remaining2_df = pd.DataFrame([
    {"Plant": k[0], "SKU": k[1], "Remaining": v[0], "Reason": v[1]}
    for k, v in merged_reason_remaining2.items()
])
with pd.ExcelWriter(path+output_sheet, engine="openpyxl") as writer:
    net_final_lib_df.to_excel(writer, sheet_name="1st Allocation", index=False)
    merged_reason_remaining1_df.to_excel(writer, sheet_name="Remaining Reason 1", index=False)
    net_net_final_lib_df.to_excel(writer, sheet_name="Final Allocation", index=False)
    remaining_machines_df.to_excel(writer, sheet_name="Remaining Machines", index=False)
    remaining_tools_df.to_excel(writer, sheet_name="Remaining Tools", index=False)
    merged_reason_remaining2_df.to_excel(writer, sheet_name="Net Remaining Reason", index=False)
print(net_final_lib_df)
print(merged_reason_remaining1_df)
print(net_net_final_lib_df)
print(remaining_machines_df)
print(remaining_tools_df)
print(merged_reason_remaining2_df)
