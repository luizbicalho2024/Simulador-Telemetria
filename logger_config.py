# logger_config.py
import logging
import sys

def setup_logger():
    """Configura e retorna um logger formatado."""
    logger = logging.getLogger("SimuladorApp")
    
    # Evita adicionar múltiplos handlers se a função for chamada várias vezes
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Cria um handler que envia os logs para o terminal (ou logs do Streamlit Cloud)
        handler = logging.StreamHandler(sys.stdout)
        
        # Define o formato do log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Cria uma instância global do logger para ser importada por outros módulos
log = setup_logger()
