/* KFC 门店分布看板
 * - 注册省级 GeoJSON 为底图（geo 组件）
 * - 省份区域按门店数手动着色（免 visualMap，缩放同步不出错）
 * - 单店散点叠加在 geo 上
 * - 省份 / 城市 TOP15 条形图
 * 坐标数据完全来自本地 stores.json，无需任何 API Key。
 */
(function () {
  "use strict";

  var GEO_URL = "../assets/geo/provinces.geojson";
  var DATA_URL = "assets/stores.json";

  function fmt(n) { return (n || 0).toLocaleString("zh-CN"); }

  function cleanName(name) {
    return name
      .replace(/(省|市|自治区|特别行政区|壮族|回族|维吾尔|藏族)$/g, "")
      .replace("内蒙古", "内蒙古");
  }

  // 颜色比例尺：0 -> 深蓝灰, 0.5 -> KFC红, 1 -> 橙
  function lerp(a, b, t) { return a + (b - a) * t; }
  function hex(c) {
    return "#" + c.map(function (x) {
      var s = Math.round(x).toString(16); return s.length === 1 ? "0" + s : s;
    }).join("");
  }
  function colorFor(t) {
    var c0 = [31, 37, 51], c1 = [228, 0, 43], c2 = [255, 122, 89], c;
    if (t < 0.5) { var k = t / 0.5; c = c0.map(function (v, i) { return lerp(v, c1[i], k); }); }
    else { var k = (t - 0.5) / 0.5; c = c1.map(function (v, i) { return lerp(v, c2[i], k); }); }
    return hex(c);
  }

  Promise.all([
    fetch(GEO_URL).then(function (r) { return r.json(); }),
    fetch(DATA_URL).then(function (r) { return r.json(); }),
  ])
    .then(function (res) { echarts.registerMap("china", res[0]); render(res[1]); })
    .catch(function (err) {
      document.getElementById("map").innerHTML = '<div class="loading">数据加载失败：' + err + "</div>";
      console.error(err);
    });

  function render(data) {
    var meta = data.meta || {};
    document.getElementById("st-total").textContent = fmt(meta.total);
    document.getElementById("st-prov").textContent = meta.provinces_covered || 0;
    document.getElementById("st-city").textContent = meta.cities_covered || 0;
    var topProv = (data.province_counts || [])[0];
    document.getElementById("st-top").textContent = topProv
      ? cleanName(topProv.name) + " " + fmt(topProv.value) : "—";

    var provMap = {};
    (data.province_counts || []).forEach(function (p) { provMap[p.name] = p.value; });
    var maxV = Math.max.apply(null, (data.province_counts || []).map(function (d) { return d.value; }).concat([1]));

    var regions = (data.province_counts || []).map(function (p) {
      return {
        name: p.name,
        itemStyle: { areaColor: colorFor(p.value / maxV) },
        emphasis: { itemStyle: { areaColor: "#2b3a55" } },
      };
    });

    var mapChart = echarts.init(document.getElementById("map"));
    mapChart.setOption({
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        formatter: function (p) {
          if (p.seriesType === "scatter") return p.name + "<br/>坐标: " + p.value[0] + ", " + p.value[1];
          var v = provMap[p.name];
          return p.name + "<br/>门店数: " + (v != null ? fmt(v) : "—");
        },
      },
      geo: {
        map: "china",
        roam: true,
        zoom: 1.15,
        scaleLimit: { min: 1, max: 8 },
        itemStyle: { areaColor: "#161b27", borderColor: "#3a445c", borderWidth: 0.6 },
        emphasis: { itemStyle: { areaColor: "#243049" }, label: { show: false } },
        regions: regions,
      },
      series: [{
        name: "门店",
        type: "scatter",
        coordinateSystem: "geo",
        data: (data.stores || []).map(function (s) { return { name: s.name, value: [s.lng, s.lat] }; }),
        symbolSize: 3,
        itemStyle: { color: "rgba(255,122,89,0.5)" },
        silent: true,
      }],
    });

    // ---------- 条形图（省份 TOP15） ----------
    var barProvChart = echarts.init(document.getElementById("barProv"));
    var topProv = (data.province_counts || []).slice(0, 15).reverse();
    barProvChart.setOption({
      backgroundColor: "transparent",
      grid: { left: 6, right: 34, top: 8, bottom: 6, containLabel: true },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      xAxis: { type: "value", axisLabel: { color: "#9aa3b2" }, splitLine: { lineStyle: { color: "#222a38" } } },
      yAxis: {
        type: "category",
        data: topProv.map(function (d) { return cleanName(d.name); }),
        axisLabel: { color: "#cdd3df", fontSize: 11 },
        axisLine: { lineStyle: { color: "#2a3142" } },
      },
      series: [{
        type: "bar",
        data: topProv.map(function (d) { return d.value; }),
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: "#e4002b" }, { offset: 1, color: "#ff7a59" }]) },
        label: { show: true, position: "right", color: "#cdd3df", fontSize: 11 },
      }],
    });

    // ---------- 条形图（城市 TOP15） ----------
    var barCityChart = echarts.init(document.getElementById("barCity"));
    var topCity = (data.city_counts || []).slice(0, 15).reverse();
    barCityChart.setOption({
      backgroundColor: "transparent",
      grid: { left: 6, right: 34, top: 8, bottom: 6, containLabel: true },
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      xAxis: { type: "value", axisLabel: { color: "#9aa3b2" }, splitLine: { lineStyle: { color: "#222a38" } } },
      yAxis: {
        type: "category",
        data: topCity.map(function (d) { return d.name; }),
        axisLabel: { color: "#cdd3df", fontSize: 11 },
        axisLine: { lineStyle: { color: "#2a3142" } },
      },
      series: [{
        type: "bar",
        data: topCity.map(function (d) { return d.value; }),
        itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: "#b5179e" }, { offset: 1, color: "#f72585" }]) },
        label: { show: true, position: "right", color: "#cdd3df", fontSize: 11 },
      }],
    });

    window.addEventListener("resize", function () {
      mapChart.resize(); barProvChart.resize(); barCityChart.resize();
    });
  }
})();
