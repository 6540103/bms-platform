package com.ruoyi.system.service.impl;

import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.system.mapper.BmsRealtimeDataMapper;
import com.ruoyi.system.domain.BmsRealtimeData;
import com.ruoyi.system.service.IBmsRealtimeDataService;

/**
 * BMS电池实时数据Service业务层处理
 */
@Service
public class BmsRealtimeDataServiceImpl implements IBmsRealtimeDataService
{
    @Autowired
    private BmsRealtimeDataMapper bmsRealtimeDataMapper;

    @Override
    public BmsRealtimeData selectBmsRealtimeDataById(Long id)
    {
        return bmsRealtimeDataMapper.selectBmsRealtimeDataById(id);
    }

    @Override
    public List<BmsRealtimeData> selectBmsRealtimeDataList(BmsRealtimeData bmsRealtimeData)
    {
        return bmsRealtimeDataMapper.selectBmsRealtimeDataList(bmsRealtimeData);
    }

    @Override
    public int insertBmsRealtimeData(BmsRealtimeData bmsRealtimeData)
    {
        return bmsRealtimeDataMapper.insertBmsRealtimeData(bmsRealtimeData);
    }

    @Override
    public BmsRealtimeData selectLatest()
    {
        return bmsRealtimeDataMapper.selectLatest();
    }

    @Override
    public int deleteBmsRealtimeDataByIds(Long[] ids)
    {
        return bmsRealtimeDataMapper.deleteBmsRealtimeDataByIds(ids);
    }
}
