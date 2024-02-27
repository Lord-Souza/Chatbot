package com.example.demo.controller;

import com.example.demo.entities.AtendimentoPacienteV;
import com.example.demo.repositories.AtendimentPacienteRepositories;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/bot")
public class CustomBotController {
    @Autowired
    private AtendimentPacienteRepositories atendimentPacienteRepositories;

    @GetMapping("/getAtendimentos")
    public ResponseEntity<List<AtendimentoPacienteV>> findAll(){
        LocalDate last60Days = LocalDate.now().minusDays(60);
        List<AtendimentoPacienteV> obj = atendimentPacienteRepositories.findAllByDtEntradaAfter(last60Days);
        return ResponseEntity.ok().body(obj);
    }
}
