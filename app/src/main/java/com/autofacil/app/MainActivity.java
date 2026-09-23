package com.autofacil.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class MainActivity extends Activity {
    private static final int PICK_FILE=1001;
    private TextView out,status,percent; private Button run,choose; private ProgressBar progress;
    private String resultsText=null;
    @Override public void onCreate(Bundle b){ super.onCreate(b);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setPadding(24,20,24,20); root.setBackgroundColor(Color.rgb(106,27,154));
        root.addView(text("☘  AutoFácil",30,true)); root.addView(text("Lotofácil • jogo escolhido pelo sistema",16,true));
        choose=new Button(this); choose.setText("ESCOLHER ARQUIVO DE RESULTADOS"); choose.setOnClickListener(v->pick()); root.addView(choose);
        run=new Button(this); run.setText("GERAR OS 2 JOGOS"); run.setEnabled(false); run.setOnClickListener(v->executar()); root.addView(run);
        status=text("Selecione o TXT/CSV dos resultados.",17,false); root.addView(status);
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal); progress.setMax(100); progress.setProgress(0); root.addView(progress,new LinearLayout.LayoutParams(-1,42));
        percent=text("0%",18,true); root.addView(percent);
        out=text("1) 250.000 candidatos sorteados\n2) universo completo: 3.268.760 combinações",16,false); ScrollView scroll=new ScrollView(this); scroll.addView(out); root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1f)); setContentView(root);
    }
    private TextView text(String s,int size,boolean center){ TextView t=new TextView(this); t.setText(s); t.setTextSize(size); t.setTextColor(Color.WHITE); t.setPadding(4,8,4,10); if(center)t.setGravity(Gravity.CENTER); return t; }
    private void pick(){ Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT); i.addCategory(Intent.CATEGORY_OPENABLE); i.setType("text/*"); startActivityForResult(i,PICK_FILE); }
    @Override protected void onActivityResult(int req,int res,Intent data){ super.onActivityResult(req,res,data); if(req==PICK_FILE&&res==RESULT_OK&&data!=null&&data.getData()!=null) load(data.getData()); }
    private void load(Uri uri){ try{ StringBuilder sb=new StringBuilder(); BufferedReader br=new BufferedReader(new InputStreamReader(getContentResolver().openInputStream(uri))); String line; while((line=br.readLine())!=null)sb.append(line).append('\n'); br.close(); resultsText=sb.toString(); status.setText("Arquivo carregado. Pronto para iniciar."); out.setText("Toque em GERAR OS 2 JOGOS."); run.setEnabled(true); progress.setProgress(0); percent.setText("0%"); }catch(Exception e){ out.setText("ERRO AO LER ARQUIVO: "+e); } }
    private void ui(String s,int pct,String detalhe){ runOnUiThread(()->{ status.setText(s); progress.setProgress(pct); percent.setText(pct+"%"); if(detalhe!=null) out.setText(detalhe); }); }
    private void executar(){ if(resultsText==null)return; run.setEnabled(false); choose.setEnabled(false); ui("Preparando histórico...",0,"Motor Python iniciado. O andamento será mostrado aqui.");
        new Thread(()->{ try{ Python py=Python.getInstance(); PyObject eng=py.getModule("autofacil_engine"); String ini=eng.callAttr("iniciar",resultsText).toString(); if(ini.startsWith("ERRO|")){ ui("Erro no arquivo",0,ini.substring(5)); return; }
            ui("ETAPA 1/2 — analisando 250.000 candidatos sorteados",0,ini);
            boolean done=false; while(!done){ String[] p=eng.callAttr("passo_250",5000).toString().split("\\|"); int feito=Integer.parseInt(p[0]), total=Integer.parseInt(p[1]); done=p[2].equals("1"); int pct=(int)((feito*100L)/total); ui("ETAPA 1/2 — sorteados: "+feito+" / "+total,pct,"Calculando primeiro jogo...\n\nProgresso: "+pct+"%"); }
            String jogo1=eng.callAttr("resultado_250").toString(); ui("ETAPA 1/2 CONCLUÍDA — primeiro jogo gerado",100,jogo1+"\n\nPreparando universo completo...");
            eng.callAttr("iniciar_universo"); done=false; while(!done){ String[] p=eng.callAttr("passo_universo",20000).toString().split("\\|"); int feito=Integer.parseInt(p[0]), total=Integer.parseInt(p[1]); done=p[2].equals("1"); int pct=(int)((feito*100L)/total); ui("ETAPA 2/2 — universo: "+feito+" / "+total,pct,jogo1+"\n\n--------------------------------\nSEGUNDO JOGO EM CÁLCULO\n"+feito+" de "+total+" combinações\nProgresso: "+pct+"%"); }
            String finalTxt=eng.callAttr("resultado_final").toString(); ui("CONCLUÍDO — os 2 jogos foram gerados",100,finalTxt);
        }catch(Exception e){ ui("ERRO",0,"ERRO: "+e); } finally{ runOnUiThread(()->{run.setEnabled(true);choose.setEnabled(true);}); } }).start();
    }
}
