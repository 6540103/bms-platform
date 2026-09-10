package com.ruoyi.system.mapper;

import java.util.List;
import com.ruoyi.system.domain.BmsRealtimeData;

/**
 * BMS电池实时数据Mapper接口
 */
public interface BmsRealtimeDataMapper
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
     * 获取最新一条记录
     */
    public BmsRealtimeData selectLatest();

    /**
     * 批量删除
     */
    public int deleteBmsRealtimeDataByIds(Long[] ids);
}
