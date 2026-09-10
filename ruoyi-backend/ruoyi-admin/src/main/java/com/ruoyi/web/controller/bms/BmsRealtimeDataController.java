package com.ruoyi.web.controller.bms;

import java.util.List;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.system.domain.BmsRealtimeData;
import com.ruoyi.system.service.IBmsRealtimeDataService;

/**
 * BMS电池实时数据Controller
 */
@RestController
@RequestMapping("/bms/realtime")
public class BmsRealtimeDataController extends BaseController
{
    @Autowired
    private IBmsRealtimeDataService bmsRealtimeDataService;

    /**
     * 查询BMS电池实时数据列表
     */
    @GetMapping("/list")
    public TableDataInfo list(BmsRealtimeData bmsRealtimeData)
    {
        startPage();
        List<BmsRealtimeData> list = bmsRealtimeDataService.selectBmsRealtimeDataList(bmsRealtimeData);
        return getDataTable(list);
    }

    /**
     * 获取最新一条电池数据
     */
    @GetMapping("/latest")
    public AjaxResult getLatest()
    {
        BmsRealtimeData data = bmsRealtimeDataService.selectLatest();
        return success(data);
    }

    /**
     * 导出BMS电池实时数据列表
     */
    @Log(title = "BMS电池实时数据", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, BmsRealtimeData bmsRealtimeData)
    {
        List<BmsRealtimeData> list = bmsRealtimeDataService.selectBmsRealtimeDataList(bmsRealtimeData);
        ExcelUtil<BmsRealtimeData> util = new ExcelUtil<BmsRealtimeData>(BmsRealtimeData.class);
        util.exportExcel(response, list, "BMS电池实时数据");
    }

    /**
     * 获取BMS电池实时数据详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id)
    {
        return success(bmsRealtimeDataService.selectBmsRealtimeDataById(id));
    }

    /**
     * 新增BMS电池实时数据
     */
    @Log(title = "BMS电池实时数据", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody BmsRealtimeData bmsRealtimeData)
    {
        return toAjax(bmsRealtimeDataService.insertBmsRealtimeData(bmsRealtimeData));
    }

    /**
     * 删除BMS电池实时数据
     */
    @Log(title = "BMS电池实时数据", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids)
    {
        return toAjax(bmsRealtimeDataService.deleteBmsRealtimeDataByIds(ids));
    }
}
