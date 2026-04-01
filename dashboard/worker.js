// Web Worker for Excel parsing
let processedCount = 0;
let totalRecords = 0;

self.onmessage = function(e) {
    const { action, data } = e.data;
    
    if (action === 'parse') {
        const { buffer, filename } = data;
        try {
            // 使用 SheetJS 解析 Excel
            importScripts('https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js');
            
            const workbook = XLSX.read(new Uint8Array(buffer), { type: 'array' });
            const sheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[sheetName];
            
            // 转换为 JSON（分块处理）
            const jsonData = XLSX.utils.sheet_to_json(worksheet);
            totalRecords = jsonData.length;
            
            // 分批次发送数据回主线程
            const CHUNK_SIZE = 10000;
            for (let i = 0; i < jsonData.length; i += CHUNK_SIZE) {
                const chunk = jsonData.slice(i, i + CHUNK_SIZE);
                processedCount += chunk.length;
                
                self.postMessage({
                    type: 'chunk',
                    data: chunk,
                    progress: Math.min(100, Math.round((processedCount / totalRecords) * 100)),
                    total: totalRecords,
                    processed: processedCount,
                    filename: filename
                });
                
                // 避免阻塞
                if (i + CHUNK_SIZE < jsonData.length) {
                    self.postMessage({ type: 'continue' });
                }
            }
            
            self.postMessage({
                type: 'complete',
                total: totalRecords,
                filename: filename
            });
            
        } catch (error) {
            self.postMessage({
                type: 'error',
                error: error.message,
                filename: filename
            });
        }
    }
    
    if (action === 'reset') {
        processedCount = 0;
        totalRecords = 0;
    }
};
