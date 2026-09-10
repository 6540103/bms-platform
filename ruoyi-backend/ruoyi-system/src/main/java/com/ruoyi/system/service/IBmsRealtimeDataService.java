package com.ruoyi.system.service;

import java.util.List;
import com.ruoyi.system.domain.BmsRealtimeData;

/**
 * BMS电池实时数据Service接口
 */
public interface IBmsRealtimeDataService
{
    /**
     * 查询BMS电池实时数据
     */
    public BmsRealtimeData selectBmsRealtimeDataById(Long id);

    /**
     * 查询BMS电池实时数据列表
     */
    public List<BmsRealtimeData> selectBmsRealtimeDataList(BmsRealtimeData bmsRealtimeData);

    /**
     * 新增BMS电池实时数据
     */
    public int insertBmsRealtimeData(BmsRealtimeData bmsRealtimeData);

    /**
     * 获取最新一条数据
     */
    public BmsRealtimeData selectLatest();

    /**
     * 批量删除
     */
    public int deleteBmsRealtimeDataByIds(Long[] ids);
}
