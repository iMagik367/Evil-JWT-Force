use sysinfo::{System, SystemExt, ProcessExt, Pid};
use chrono::Local;
use serde::{Serialize, Deserialize};
use serde_json;
use log::{info, error};
use env_logger;
use std::fs::OpenOptions;
use std::io::Write;
use std::thread;
use std::time::Duration;
use std::env;

#[derive(Serialize, Deserialize, Debug)]
struct ProcessMetrics {
    timestamp: String,
    pid: i32,
    cpu_usage: f32,
    memory_usage_mb: f64,
    name: String,
}

fn main() {
    env_logger::init();
    info!("Iniciando monitor de processos em Rust");
    
    let args: Vec<String> = env::args().collect();
    let pid = if args.len() > 1 {
        args[1].parse::<i32>().unwrap_or_else(|_| {
            error!("PID inválido fornecido. Usando PID atual.");
            std::process::id() as i32
        })
    } else {
        std::process::id() as i32
    };
    
    info!("Monitorando PID: {}", pid);
    let output_file = "ai_system/data/process_metrics.json".to_string();
    
    // Cria ou abre o arquivo para escrita
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&output_file)
        .unwrap_or_else(|e| {
            error!("Erro ao abrir arquivo {}: {}", output_file, e);
            panic!("Não foi possível abrir o arquivo de saída");
        });
    
    let mut system = System::new_all();
    loop {
        system.refresh_all();
        if let Some(process) = system.process(Pid::from(pid as usize)) {
            let cpu_usage = process.cpu_usage();
            let memory_usage = process.memory() as f64 / 1024.0 / 1024.0; // Convertendo para MB
            let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
            let name = process.name().to_string();
            
            let metrics = ProcessMetrics {
                timestamp,
                pid,
                cpu_usage,
                memory_usage_mb: memory_usage,
                name,
            };
            
            let json_str = serde_json::to_string(&metrics).unwrap_or_else(|e| {
                error!("Erro ao serializar métricas: {}", e);
                String::from("{}")
            });
            
            if let Err(e) = writeln!(file, "{}", json_str) {
                error!("Erro ao escrever no arquivo: {}", e);
            } else {
                info!("Métricas coletadas para PID {}: CPU={}%, Memória={}MB", pid, cpu_usage, memory_usage);
            }
        } else {
            error!("Processo com PID {} não encontrado.", pid);
            break;
        }
        
        thread::sleep(Duration::from_secs(5));
    }
} 