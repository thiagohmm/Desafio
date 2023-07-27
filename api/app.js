const express = require('express');
const axios = require('axios');
const amqp = require('amqplib');

const app = express();
const PORT = 3000;

app.use(express.json());

// Função para enviar a lista de CPFs e o token Bearer para o RabbitMQ
async function sendToRabbitMQ(cpfList, token) {
  try {
    const connection = await amqp.connect('amqp://localhost');
    const channel = await connection.createChannel();
    const queue = 'cpf_queue';

    await channel.assertQueue(queue, { durable: true });

    const message = JSON.stringify({ cpfList });

    channel.sendToQueue(queue, Buffer.from(message), { persistent: true });

    console.log('Mensagem enviada para o RabbitMQ:', message);

    setTimeout(() => {
      connection.close();
    }, 500);
  } catch (error) {
    console.error('Erro ao enviar mensagem para o RabbitMQ:', error.message);
  }
}

function testarListaDeCPFs(cpfList) {
  const cpfRegex = /^\d{3}\.\d{3}\.\d{3}-\d{2}$/;
  const cpfOK = []
  for (const cpf of cpfList) {
    if (cpfRegex.test(cpf)) {

      cpfOK.push(cpf);
    }
  }

  return cpfOK;
}

// Rota para receber a lista de CPFs
app.post('/send-cpfs', async (req, res) => {
  const { cpfList } = req.body;

  // Faz o request para a API remota (substitua a URL abaixo pela sua API remota)
  try {

    const testedCpf = await testarListaDeCPFs(cpfList)

    // Chama a função para enviar os dados para o RabbitMQ
    sendToRabbitMQ(testedCpf);

    res.status(200).json({ message: 'Requisição enviada com sucesso!' });
  } catch (error) {
    res.status(error.response.status || 500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Servidor rodando na porta ${PORT}`);
});
