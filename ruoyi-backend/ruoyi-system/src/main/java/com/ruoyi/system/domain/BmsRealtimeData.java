package com.ruoyi.system.domain;

import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseEntity;

/**
 * BMS电池实时数据对象 bms_realtime_data
 */
public class BmsRealtimeData extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    private Long id;
    private Double simTime;
    private Double packVoltage;
    private Double current;
    private Double power;
    private Double soc;
    private Double soh;
    private Double minCellVoltage;
    private Double maxCellVoltage;
    private Double voltageImbalance;
    private Double temperature;
    private Double ambientTemp;
    private String status;
    private String cellVoltage;
    private String cellSoc;
    private Double capacityAh;
    private Integer cycleCount;
    private Integer numCells;

    /** BMS完整状态JSON (保护/均衡/SOC估算/SOH) */
    private String bmsStatus;

    public void setId(Long id) { this.id = id; }
    public Long getId() { return id; }
    public void setSimTime(Double simTime) { this.simTime = simTime; }
    public Double getSimTime() { return simTime; }
    public void setPackVoltage(Double packVoltage) { this.packVoltage = packVoltage; }
    public Double getPackVoltage() { return packVoltage; }
    public void setCurrent(Double current) { this.current = current; }
    public Double getCurrent() { return current; }
    public void setPower(Double power) { this.power = power; }
    public Double getPower() { return power; }
    public void setSoc(Double soc) { this.soc = soc; }
    public Double getSoc() { return soc; }
    public void setSoh(Double soh) { this.soh = soh; }
    public Double getSoh() { return soh; }
    public void setMinCellVoltage(Double minCellVoltage) { this.minCellVoltage = minCellVoltage; }
    public Double getMinCellVoltage() { return minCellVoltage; }
    public void setMaxCellVoltage(Double maxCellVoltage) { this.maxCellVoltage = maxCellVoltage; }
    public Double getMaxCellVoltage() { return maxCellVoltage; }
    public void setVoltageImbalance(Double voltageImbalance) { this.voltageImbalance = voltageImbalance; }
    public Double getVoltageImbalance() { return voltageImbalance; }
    public void setTemperature(Double temperature) { this.temperature = temperature; }
    public Double getTemperature() { return temperature; }
    public void setAmbientTemp(Double ambientTemp) { this.ambientTemp = ambientTemp; }
    public Double getAmbientTemp() { return ambientTemp; }
    public void setStatus(String status) { this.status = status; }
    public String getStatus() { return status; }
    public void setCellVoltage(String cellVoltage) { this.cellVoltage = cellVoltage; }
    public String getCellVoltage() { return cellVoltage; }
    public void setCellSoc(String cellSoc) { this.cellSoc = cellSoc; }
    public String getCellSoc() { return cellSoc; }
    public void setCapacityAh(Double capacityAh) { this.capacityAh = capacityAh; }
    public Double getCapacityAh() { return capacityAh; }
    public void setCycleCount(Integer cycleCount) { this.cycleCount = cycleCount; }
    public Integer getCycleCount() { return cycleCount; }
    public void setNumCells(Integer numCells) { this.numCells = numCells; }
    public Integer getNumCells() { return numCells; }
    public void setBmsStatus(String bmsStatus) { this.bmsStatus = bmsStatus; }
    public String getBmsStatus() { return bmsStatus; }

    @Override
    public String toString() {
        return "BmsRealtimeData{id=" + id + ", soc=" + soc + ", status='" + status + "'}";
    }
}
